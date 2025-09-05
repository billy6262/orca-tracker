import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_curve, auc, precision_recall_curve, confusion_matrix
from sklearn.calibration import calibration_curve
import warnings
warnings.filterwarnings('ignore')

# Set plot styles
plt.style.use('default')
sns.set_palette("husl")

class ModelMetricsVisualizer:
    """
    Class for generating model performance plots and metrics.
    """
    
    def __init__(self, save_dir='./model_metrics/'):
        """Set up the output directory."""
        import os
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
        
    def plot_roc_curves(self, models, X_test, y_test, bucket_names, save_name='roc_curves.png'):
        """Plot ROC curves for the zone models."""
        
        # Figure out subplot layout
        fig, axes = plt.subplots(1, len(models), figsize=(6*len(models), 5))
        if len(models) == 1:
            axes = [axes]
        
        all_auc_scores = []
        
        for bucket_idx, (bucket_models, ax) in enumerate(zip(models.values(), axes)):
            bucket_name = bucket_names[bucket_idx]
            y_bucket = y_test.filter(regex=f'bucket_{bucket_idx}_')
            
            zone_aucs = []
            
            # Loop through each zone model and calculate ROC
            for zone_col, model in bucket_models.items():
                if zone_col in y_bucket.columns:
                    y_true = y_bucket[zone_col]
                    
                    # Skip zones with no positive examples
                    if y_true.sum() > 0:
                        try:
                            y_pred_proba = model.predict_proba(X_test)[:, 1]
                            fpr, tpr, _ = roc_curve(y_true, y_pred_proba)
                            roc_auc = auc(fpr, tpr)
                            zone_aucs.append(roc_auc)
                            
                            zone_name = zone_col.split('_zone_')[-1]
                            ax.plot(fpr, tpr, linewidth=1, alpha=0.7, 
                                   label=f'Zone {zone_name} (AUC = {roc_auc:.3f})')
                        except:
                            # Sometimes models fail, just skip them
                            continue
            
            # Add the diagonal reference line
            ax.plot([0, 1], [0, 1], 'k--', linewidth=1, alpha=0.5)
            ax.set_xlim([0.0, 1.0])
            ax.set_ylim([0.0, 1.05])
            ax.set_xlabel('False Positive Rate')
            ax.set_ylabel('True Positive Rate')
            ax.set_title(f'ROC Curves - {bucket_name}\nMean AUC = {np.mean(zone_aucs):.3f}')
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
            ax.grid(True, alpha=0.3)
            
            all_auc_scores.extend(zone_aucs)
        
        plt.suptitle(f'ROC Curves by Time Bucket\nOverall Mean AUC = {np.mean(all_auc_scores):.3f}', 
                     fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(f"{self.save_dir}{save_name}", dpi=300, bbox_inches='tight')
        plt.close()
        
        return np.mean(all_auc_scores), all_auc_scores
    
    def plot_precision_recall_curves(self, models, X_test, y_test, bucket_names, save_name='precision_recall_curves.png'):
        """PR curves - more useful than ROC for imbalanced data."""
        
        fig, axes = plt.subplots(1, len(models), figsize=(6*len(models), 5))
        if len(models) == 1:
            axes = [axes]
        
        all_ap_scores = []
        
        for bucket_idx, (bucket_models, ax) in enumerate(zip(models.values(), axes)):
            bucket_name = bucket_names[bucket_idx]
            y_bucket = y_test.filter(regex=f'bucket_{bucket_idx}_')
            
            zone_aps = []
            
            for zone_col, model in bucket_models.items():
                if zone_col in y_bucket.columns:
                    y_true = y_bucket[zone_col]
                    
                    if y_true.sum() > 0:
                        try:
                            y_pred_proba = model.predict_proba(X_test)[:, 1]
                            precision, recall, _ = precision_recall_curve(y_true, y_pred_proba)
                            ap_score = auc(recall, precision)
                            zone_aps.append(ap_score)
                            
                            zone_name = zone_col.split('_zone_')[-1]
                            ax.plot(recall, precision, linewidth=1, alpha=0.7,
                                   label=f'Zone {zone_name} (AP = {ap_score:.3f})')
                        except:
                            continue
            
            # Show the baseline (random classifier performance)
            baseline = y_bucket.sum().sum() / len(y_bucket)
            ax.axhline(y=baseline, color='k', linestyle='--', alpha=0.5, label=f'Baseline = {baseline:.3f}')
            
            ax.set_xlim([0.0, 1.0])
            ax.set_ylim([0.0, 1.05])
            ax.set_xlabel('Recall')
            ax.set_ylabel('Precision')
            ax.set_title(f'Precision-Recall - {bucket_name}\nMean AP = {np.mean(zone_aps):.3f}')
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
            ax.grid(True, alpha=0.3)
            
            all_ap_scores.extend(zone_aps)
        
        plt.suptitle(f'Precision-Recall Curves by Time Bucket\nOverall Mean AP = {np.mean(all_ap_scores):.3f}', 
                     fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(f"{self.save_dir}{save_name}", dpi=300, bbox_inches='tight')
        plt.close()
        
        return np.mean(all_ap_scores), all_ap_scores
    
    def plot_feature_importance(self, models, feature_columns, save_name='feature_importance.png'):
        """Feature importance plots. Aggregated across all models."""
        
        # Collect importance from all models
        all_importances = []
        model_names = []
        
        for bucket_idx, zone_models in models.items():
            for zone_col, model in zone_models.items():
                zone_name = zone_col.split('_zone_')[-1]
                bucket_name = f"Bucket {bucket_idx}"
                model_names.append(f"{bucket_name}-Zone {zone_name}")
                all_importances.append(model.feature_importances_)
        
        if not all_importances:
            print("No feature importance data available")
            return
        
        # Calculate stats
        importance_df = pd.DataFrame(all_importances, columns=feature_columns)
        mean_importance = importance_df.mean()
        std_importance = importance_df.std()
        
        # Two-panel plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Left plot: bar chart with error bars
        top_features = mean_importance.nlargest(10)
        top_std = std_importance[top_features.index]
        
        bars = ax1.barh(range(len(top_features)), top_features.values, 
                       xerr=top_std.values, capsize=3, alpha=0.7)
        ax1.set_yticks(range(len(top_features)))
        ax1.set_yticklabels(top_features.index)
        ax1.set_xlabel('Mean Feature Importance')
        ax1.set_title('Top 10 Features by Average Importance\n(with standard deviation)')
        ax1.grid(True, alpha=0.3)
        
        # Add value labels
        for i, (bar, val, std_val) in enumerate(zip(bars, top_features.values, top_std.values)):
            ax1.text(val + std_val + 0.001, i, f'{val:.3f}±{std_val:.3f}', 
                    va='center', fontsize=8)
        
        # Right plot: heatmap of importance across models
        top_10_features = mean_importance.nlargest(10).index
        heatmap_data = importance_df[top_10_features].T
        
        sns.heatmap(heatmap_data, ax=ax2, cmap='viridis', cbar=True, 
                   xticklabels=False, yticklabels=top_10_features)
        ax2.set_title('Feature Importance Across All Models\n(Top 10 Features)')
        ax2.set_xlabel('Individual Models')
        
        plt.tight_layout()
        plt.savefig(f"{self.save_dir}{save_name}", dpi=300, bbox_inches='tight')
        plt.close()
        
        return mean_importance, std_importance
    
    def plot_model_performance_summary(self, models, X_test, y_test, bucket_names, save_name='performance_summary.png'):
        """Big summary plot with 6 panels. This function got messy but it works."""
        
        # Extract performance metrics for all zone models
        performance_data = []
        
        for bucket_idx, zone_models in models.items():
            bucket_name = bucket_names[bucket_idx]
            y_bucket = y_test.filter(regex=f'bucket_{bucket_idx}_')
            
            for zone_col, model in zone_models.items():
                if zone_col in y_bucket.columns:
                    y_true = y_bucket[zone_col]
                    
                    if y_true.sum() > 0:
                        try:
                            y_pred = model.predict(X_test)
                            y_pred_proba = model.predict_proba(X_test)[:, 1]
                            
                            # Calculate standard metrics
                            from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
                            
                            auc_score = roc_auc_score(y_true, y_pred_proba)
                            precision = precision_score(y_true, y_pred, zero_division=0)
                            recall = recall_score(y_true, y_pred, zero_division=0)
                            f1 = f1_score(y_true, y_pred, zero_division=0)
                            
                            zone_name = zone_col.split('_zone_')[-1]
                            
                            performance_data.append({
                                'bucket': bucket_name,
                                'zone': zone_name,
                                'auc': auc_score,
                                'precision': precision,
                                'recall': recall,
                                'f1_score': f1,
                                'positive_samples': y_true.sum()
                            })
                        except:
                            # Skip failed models
                            continue
        
        if not performance_data:
            print("No performance data available")
            return
        
        perf_df = pd.DataFrame(performance_data)
        
        # 2x3 subplot grid
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        
        # Plot 1: AUC by time bucket
        bucket_auc = perf_df.groupby('bucket')['auc'].agg(['mean', 'std', 'count'])
        ax1 = axes[0, 0]
        bucket_auc['mean'].plot(kind='bar', ax=ax1, capsize=3, 
                               yerr=bucket_auc['std'], alpha=0.7)
        ax1.set_title('Mean AUC by Time Bucket')
        ax1.set_ylabel('AUC Score')
        ax1.set_xlabel('Time Bucket')
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Precision vs Recall scatter (with AUC color coding)
        ax2 = axes[0, 1]
        scatter = ax2.scatter(perf_df['recall'], perf_df['precision'], 
                             c=perf_df['auc'], s=perf_df['positive_samples']*2,
                             alpha=0.6, cmap='viridis')
        ax2.set_xlabel('Recall')
        ax2.set_ylabel('Precision')
        ax2.set_title('Precision vs Recall\n(size=positive samples, color=AUC)')
        plt.colorbar(scatter, ax=ax2, label='AUC Score')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: F1 score histogram
        ax3 = axes[0, 2]
        perf_df['f1_score'].hist(bins=20, ax=ax3, alpha=0.7, edgecolor='black')
        ax3.set_xlabel('F1 Score')
        ax3.set_ylabel('Frequency')
        ax3.set_title('F1 Score Distribution')
        ax3.axvline(perf_df['f1_score'].mean(), color='red', linestyle='--', 
                   label=f'Mean: {perf_df["f1_score"].mean():.3f}')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Top zones by AUC (limit to top 10 to avoid clutter)
        top_zones = perf_df.groupby('zone')['positive_samples'].sum().nlargest(10)
        zone_perf = perf_df[perf_df['zone'].isin(top_zones.index)].groupby('zone')['auc'].mean()
        
        ax4 = axes[1, 0]
        zone_perf.plot(kind='bar', ax=ax4, alpha=0.7)
        ax4.set_title('Mean AUC by Zone (Top 10 by Sample Count)')
        ax4.set_ylabel('Mean AUC')
        ax4.set_xlabel('Zone')
        ax4.tick_params(axis='x', rotation=45)
        ax4.grid(True, alpha=0.3)
        
        # Plot 5: Sample size vs performance relationship
        ax5 = axes[1, 1]
        ax5.scatter(perf_df['positive_samples'], perf_df['auc'], alpha=0.6)
        ax5.set_xlabel('Number of Positive Samples')
        ax5.set_ylabel('AUC Score')
        ax5.set_title('Model Performance vs Sample Size')
        ax5.set_xscale('log')  # Log scale since sample sizes vary a lot
        ax5.grid(True, alpha=0.3)
        
        # Add a trend line
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            np.log(perf_df['positive_samples']), perf_df['auc'])
        line = slope * np.log(perf_df['positive_samples']) + intercept
        ax5.plot(perf_df['positive_samples'], line, 'r--', alpha=0.8,
                label=f'R² = {r_value**2:.3f}')
        ax5.legend()
        
        # Plot 6: Average metrics comparison
        ax6 = axes[1, 2]
        metrics_summary = perf_df[['auc', 'precision', 'recall', 'f1_score']].mean()
        bars = ax6.bar(metrics_summary.index, metrics_summary.values, alpha=0.7)
        ax6.set_title('Average Performance Metrics')
        ax6.set_ylabel('Score')
        ax6.set_ylim(0, 1)
        
        # Add value labels on top of bars
        for bar, val in zip(bars, metrics_summary.values):
            ax6.text(bar.get_x() + bar.get_width()/2, val + 0.01, f'{val:.3f}',
                    ha='center', va='bottom')
        ax6.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f"{self.save_dir}{save_name}", dpi=300, bbox_inches='tight')
        plt.close()
        
        return perf_df
    
    def plot_prediction_calibration(self, models, X_test, y_test, bucket_names, save_name='calibration_plots.png'):
        """Calibration plots to check if predicted probabilities are realistic."""
        
        fig, axes = plt.subplots(1, len(models), figsize=(6*len(models), 5))
        if len(models) == 1:
            axes = [axes]
        
        for bucket_idx, (bucket_models, ax) in enumerate(zip(models.values(), axes)):
            bucket_name = bucket_names[bucket_idx]
            y_bucket = y_test.filter(regex=f'bucket_{bucket_idx}_')
            
            # Aggregate all predictions for this bucket
            all_y_true = []
            all_y_prob = []
            
            for zone_col, model in bucket_models.items():
                if zone_col in y_bucket.columns:
                    y_true = y_bucket[zone_col]
                    
                    if y_true.sum() > 0:
                        try:
                            y_pred_proba = model.predict_proba(X_test)[:, 1]
                            all_y_true.extend(y_true.values)
                            all_y_prob.extend(y_pred_proba)
                        except:
                            continue
            
            if all_y_true:
                # Calculate calibration curve (splits predictions into bins)
                fraction_of_positives, mean_predicted_value = calibration_curve(
                    all_y_true, all_y_prob, n_bins=10)
                
                # Plot the calibration curve
                ax.plot(mean_predicted_value, fraction_of_positives, "s-",
                       label=f"{bucket_name}", linewidth=2)
                
                # Perfect calibration reference line
                ax.plot([0, 1], [0, 1], "k:", label="Perfectly calibrated", alpha=0.5)
                
                ax.set_xlabel('Mean Predicted Probability')
                ax.set_ylabel('Fraction of Positives')
                ax.set_title(f'Calibration Plot - {bucket_name}')
                ax.legend()
                ax.grid(True, alpha=0.3)
        
        plt.suptitle('Prediction Calibration by Time Bucket', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(f"{self.save_dir}{save_name}", dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_confusion_matrices(self, models, X_test, y_test, bucket_names, save_name='confusion_matrices.png'):
        """Confusion matrices for each time bucket."""
        
        fig, axes = plt.subplots(1, len(models), figsize=(5*len(models), 4))
        if len(models) == 1:
            axes = [axes]
        
        for bucket_idx, (bucket_models, ax) in enumerate(zip(models.values(), axes)):
            bucket_name = bucket_names[bucket_idx]
            y_bucket = y_test.filter(regex=f'bucket_{bucket_idx}_')
            
            # Combine predictions from all zones in this bucket
            all_y_true = []
            all_y_pred = []
            
            for zone_col, model in bucket_models.items():
                if zone_col in y_bucket.columns:
                    y_true = y_bucket[zone_col]
                    
                    if y_true.sum() > 0:
                        try:
                            y_pred = model.predict(X_test)
                            all_y_true.extend(y_true.values)
                            all_y_pred.extend(y_pred)
                        except:
                            continue
            
            if all_y_true:
                # Build confusion matrix
                cm = confusion_matrix(all_y_true, all_y_pred)
                
                # Plot as heatmap
                sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                           xticklabels=['No Sighting', 'Sighting'],
                           yticklabels=['No Sighting', 'Sighting'])
                ax.set_title(f'Confusion Matrix - {bucket_name}')
                ax.set_xlabel('Predicted')
                ax.set_ylabel('Actual')
        
        plt.tight_layout()
        plt.savefig(f"{self.save_dir}{save_name}", dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_comprehensive_report(self, models, X_test, y_test, bucket_names, feature_columns):
        """Run all the visualization functions and return summary stats."""
        
        # Run all the plotting functions
        mean_auc, all_aucs = self.plot_roc_curves(models, X_test, y_test, bucket_names)
        mean_ap, all_aps = self.plot_precision_recall_curves(models, X_test, y_test, bucket_names)
        mean_importance, std_importance = self.plot_feature_importance(models, feature_columns)
        perf_df = self.plot_model_performance_summary(models, X_test, y_test, bucket_names)
        self.plot_prediction_calibration(models, X_test, y_test, bucket_names)
        self.plot_confusion_matrices(models, X_test, y_test, bucket_names)
        
        # Package up the results
        summary_stats = {
            'mean_auc': mean_auc,
            'std_auc': np.std(all_aucs),
            'mean_ap': mean_ap,
            'std_ap': np.std(all_aps),
            'top_features': mean_importance.nlargest(5).to_dict(),
            'total_models': sum(len(bucket_models) for bucket_models in models.values()),
            'performance_df': perf_df
        }

        
        return summary_stats

def create_model_visualizations(models, X_test, y_test, bucket_names, feature_columns, save_dir='./model_metrics/'):
    """
    Main function to generate all the model visualization plots.
    
    Args:
        models: Dict of trained XGBoost models organized by bucket
        X_test: Test feature data
        y_test: Test target data  
        bucket_names: Names for the time buckets
        feature_columns: List of feature names
        save_dir: Where to save the plot files
    
    Returns:
        Dict with summary stats and performance info
    """
    
    visualizer = ModelMetricsVisualizer(save_dir)
    summary_stats = visualizer.generate_comprehensive_report(
        models, X_test, y_test, bucket_names, feature_columns
    )
    
    return summary_stats
