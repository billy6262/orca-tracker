import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import warnings
from model_metrics_visualization import create_model_visualizations
warnings.filterwarnings('ignore')

# DB must be online to return data
DB_CONNECTION = 'postgresql://orca:orca@localhost:5432/orca_tracker'  
engine = create_engine(DB_CONNECTION)

# Load data
df = pd.read_sql('SELECT * FROM "data_pipeline_orcasighting"', engine)
df['time'] = pd.to_datetime(df['time'])
df = df.sort_values('time').reset_index(drop=True)

# Time buckets - 6 hour windows for next 2 days
buckets = [(i, i+6) for i in range(0, 48, 6)]  
bucket_labels = [f"{start}-{end}h" for start, end in buckets]

def build_training_data(data, batch_size=5000):
    """Process entire dataset to create prediction targets"""
    
    results = []
    sorted_data = data.sort_values('time').reset_index(drop=True)
    total = len(sorted_data)
    
    print(f"Processing {total} records...")
    
    # chunk processing to avoid memory issues
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        print(f"Batch {start//batch_size + 1}/{(total-1)//batch_size + 1}: {start}-{end}")
        
        chunk = sorted_data.iloc[start:end].copy()
        
        for idx, row in chunk.iterrows():
            curr_time = row['time']
            
            # look ahead 48 hours
            cutoff = curr_time + pd.Timedelta(hours=48)
            future_data = sorted_data[(sorted_data['time'] > curr_time) & 
                                    (sorted_data['time'] <= cutoff)].copy()
            
            if len(future_data) == 0:
                continue
                
            future_data['hours_from_now'] = (future_data['time'] - curr_time).dt.total_seconds() / 3600
            
            # build targets for each time bucket
            target_dict = {}
            
            for bucket_id, (start_hr, end_hr) in enumerate(buckets):
                bucket_data = future_data[(future_data['hours_from_now'] > start_hr) & 
                                        (future_data['hours_from_now'] <= end_hr)]
                
                # check each zone for actual sightings
                for zone_name in data['zone'].unique():
                    col_name = f"bucket_{bucket_id}_{start_hr}h_zone_{zone_name}"
                    
                    zone_sightings = bucket_data[(bucket_data['zone'] == zone_name) & 
                                               (bucket_data['present'] == True)]
                    
                    target_dict[col_name] = 1 if len(zone_sightings) > 0 else 0
            
            # combine row data with targets
            row_dict = row.to_dict()
            row_dict.update(target_dict)
            results.append(row_dict)
        
        # memory cleanup
        if len(results) % 50000 == 0 and len(results) > 0: # print progress for longer runs
            print(f"  {len(results)} examples processed...")
    
    return pd.DataFrame(results)

training_data = build_training_data(df, batch_size=5000)
target_columns = [col for col in training_data.columns if col.startswith('bucket_')]

# Feature setup
features = [
    'month', 'dayOfWeek', 'hour', 'isWeekend', 'sunUp',
    'reportsIn5h', 'reportsIn24h', 'reportsInAdjacentZonesIn5h', 'reportsInAdjacentPlusZonesIn5h',
    'count', 'ZoneNumber_id', 'present' 
]

# convert timedelta to hours (more linear approach for the model)
training_data['hours_since_last'] = training_data['timeSinceLastSighting'].dt.total_seconds() / 3600
features.append('hours_since_last')

# encode zones as numbers
encoder = LabelEncoder()
training_data['zone_num'] = encoder.fit_transform(training_data['zone'])
features.append('zone_num')

# xgboost needs ints not bools
training_data['present'] = training_data['present'].astype(int)

# handle NaNs - just fill with median for numeric cols
for col in features:
    if training_data[col].dtype in ['float64', 'int64']:
        training_data[col] = training_data[col].fillna(training_data[col].median())

X = training_data[features].copy()


# group targets by bucket
bucket_targets = {}
for i in range(len(buckets)):
    cols = [col for col in target_columns if col.startswith(f'bucket_{i}_')]
    bucket_targets[i] = cols

def train_bucket_models(X_train, y_targets, bucket_name):
    """Train models for each zone in a time bucket"""
    # simple 80/20 split by time (chronological)
    split_point = int(len(X_train) * 0.8)
    X_tr, X_te = X_train.iloc[:split_point], X_train.iloc[split_point:]
    y_tr, y_te = y_targets.iloc[:split_point], y_targets.iloc[split_point:]
    
    # store models for each zone
    zone_models = {}
    zone_preds = {}
    zone_probs = {}
    
    for target_col in y_targets.columns:
        y_train_zone = y_tr[target_col]
        y_test_zone = y_te[target_col]
        
        # skip if too few positive examples
        if y_train_zone.sum() < 5:
            continue
        
        # handle class imbalance
        pos = y_train_zone.sum()
        neg = len(y_train_zone) - pos
        weight = neg / pos if pos > 0 else 1

        
        # xgboost params - tuned through trial and error
        params = {
            'objective': 'binary:logistic',
            'max_depth': 7,  
            'learning_rate': 0.08, 
            'n_estimators': 200,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'scale_pos_weight': min(weight, 50),  # cap at 50
            'random_state': 42,
            'n_jobs': -1,
            'verbosity': 0,
            'reg_alpha': 0.1,
            'reg_lambda': 1.5,
            'min_child_weight': 5,
            'gamma': 0.1
        }
        
        model = xgb.XGBClassifier(**params)
        
        # try early stopping, fallback if doesn't work
        try:
            from xgboost.callback import EarlyStopping
            model.fit(X_tr, y_train_zone,
                     eval_set=[(X_te, y_test_zone)],
                     callbacks=[EarlyStopping(rounds=30)],
                     verbose=False)
        except:
            # just train normally if early stopping fails
            model.fit(X_tr, y_train_zone, verbose=False)
        
        preds = model.predict(X_te)
        probs = model.predict_proba(X_te)[:, 1]
        
        zone_models[target_col] = model
        zone_preds[target_col] = preds
        zone_probs[target_col] = probs
          
    return zone_models, zone_preds, zone_probs

print("\n=== TRAINING MODELS ===")
all_models = {}

for bucket_idx in range(len(buckets)):
    bucket_name = bucket_labels[bucket_idx]
    bucket_y = training_data[bucket_targets[bucket_idx]]
    
    print(f"\n{bucket_name}:")
    if bucket_y.sum().sum() > 0:
        models, preds, probs = train_bucket_models(X, bucket_y, bucket_name)
        all_models[bucket_idx] = models


def make_predictions(features, models, encoder, top_n=5):
    pred_results = {}
    
    for bucket_id, bucket_models in models.items():
        bucket_name = bucket_labels[bucket_id]
        
        try:
            zone_probs = {}
            
            for model_name, model in bucket_models.items():
                zone = model_name.split('_zone_')[-1]
                
                prob = model.predict_proba(features)
                zone_prob = prob[0][1] if len(prob[0]) > 1 else 0
                zone_probs[zone] = zone_prob
            
            # sort by probability
            sorted_zones = sorted(zone_probs.items(), key=lambda x: x[1], reverse=True)
            top_zones = sorted_zones[:top_n]
            
            # overall bucket probability using probabilistic OR
            overall = 0
            for _, p in zone_probs.items():
                overall = overall + p - (overall * p)
            
            pred_results[bucket_name] = {
                'top_zones': top_zones,
                'all_zones': zone_probs,
                'overall_prob': min(1.0, overall)
            }
            
                
        except Exception as e:
            # just skip if prediction fails
            pred_results[bucket_name] = {
                'top_zones': [], 
                'all_zones': {},
                'overall_prob': 0.0
            }
    
    return pred_results

# test with last sample
if len(all_models) > 0:
    test_sample = X.iloc[-1:].copy()
    test_preds = make_predictions(test_sample, all_models, encoder)



# save models
import joblib
for bucket_id, bucket_models in all_models.items():
    filename = f'orca_model_bucket_{bucket_id}.pkl'
    joblib.dump(bucket_models, filename)
    print(f"Saved {filename}")

joblib.dump(encoder, 'zone_encoder.pkl')
joblib.dump(features, 'features.pkl')

# generate visualizations
if len(all_models) > 0 and len(X) > 100:
    print("\n=== GENERATING CHARTS ===")
    
    test_size = min(0.2, 20000 / len(X))
    y_all = training_data[target_columns]
    X_train_viz, X_test_viz, y_train_viz, y_test_viz = train_test_split(
        X, y_all, test_size=test_size, random_state=42)
    
    # generating charts using the visualization module
    viz_results = create_model_visualizations(
        models=all_models,
        X_test=X_test_viz,
        y_test=y_test_viz,
        bucket_names=[bucket_labels[i] for i in all_models.keys()],
        feature_columns=features,
        save_dir='./charts/'
    )
