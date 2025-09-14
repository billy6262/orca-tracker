import React from 'react';
import figure1 from '../assets/figure1.png';
import figure2 from '../assets/figure2.png';
import figure3 from '../assets/figure3.png';
import figure41 from '../assets/figure4-1.png';
import figure42 from '../assets/figure4-2.png';
import figure43 from '../assets/figure4-3.png';
import figure5 from '../assets/figure5.png';

const TechnicalSummaryPage = () => {
  return (
    <div className="about-page" style={{ minHeight: '100vh', backgroundColor: '#f5f5f5', padding: '20px' }}>
      <div style={{ 
        maxWidth: '800px', 
        margin: '0 auto', 
        backgroundColor: 'white', 
        padding: '40px', 
        borderRadius: '8px', 
        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)', 
        lineHeight: '1.6' 
      }}>
        <h1>Technical Summary, Approach, and Applications of Machine Learning in Orca Movement Prediction in the Puget Sound</h1>
      
      <p><strong>Andrew M Dorchak</strong></p>

      <h2>Abstract</h2>
      
      <h3>Intent:</h3>
      <p>
        One of the most important questions in marine mammal conservation in the Salish Sea is predicting the movement patterns of the population. For orcas in particular, this is an important question as they are much more easily affected by changing conditions in their environment. According to research (Scott & Mayer, 2023), noise pollution substantially affects the population of orcas in the surrounding area. If it were possible to reduce noise pollution in targeted areas, this would likely help to alleviate the added stressors to existing orca populations. The key drawback to reducing noise emission is that this would inhibit commercial vessel traffic, as they are the largest emitters of marine noise. This could have a severe economic impact on many maritime communities. Machine learning could potentially provide the insight needed to implement a safeguard of this sort while minimally impacting commercial vessel traffic and allowing for commerce to continue. If provided with enough data points, this machine learning model could predict seasonal transitory patterns and the density of orca populations. Using the predictions provided, a model could be developed to help reduce noise in key areas while not restricting commercial vessels in areas where it would have little impact on orca populations.
      </p>

      <h2>Background:</h2>
      <p>
        Since before the settling of the Puget Sound, orcas have garnered a fair amount of attention from local populations. Coastal tribes of the Salish Sea often have legends referring to orcas as the spirits of hunters or fishermen, and they are readily present in tribal iconography in the area. Estimates state that pre-20th century, the resident orca population in the Salish Sea was approximately 200. In the 1970s, there was a series of orca captures for use in aquariums, where some 60 orcas were captured. This culminated in both the us and Canada passing laws prohibiting the practice. The publicity and outrage caused by this incident started many of the conservation projects currently in place.
      </p>
      <p>
        After the major captures in the 70s, the resident orca populations surged to an estimated 98 orcas in 1995. Despite the resurgence in population in the 90s, it has only been on the decline since. As mentioned before, research (Scott & Mayer, 2023) indicates that this decline in population post-1990s may be caused by an increase in commercial marine traffic. There have been various conservation projects around studying and minimizing our impact on the orca populations. Several of these conservation efforts in the past have faced harsh criticism from commercial marine industry leaders who allege that the restrictions placed on them severely restrict their ability to conduct commerce.
      </p>
      <p>
        Being able to accurately predict the movement patterns of the orca populations may well help with understanding which areas impact populations the most. Many projects endeavor to do this by using historical data, crowd-sourced reports, and hydro sonography to track orca movements. There is a sufficiently large data set to be able to draw conclusions from it, but building a comprehensive model to predict animal behavior is complex. At this point, there has not been a major push by any organization to be able to predict orca transits with a machine learning model trained on historical reports and data. Investigating the viability of this tracking method could be key to marine conservation in the Salish Sea and help to steward the ecologically keystone population of resident orcas.
      </p>

      <h2>Hypothesis</h2>
      <p>
        The impact of marine noise pollution on orca populations in the Puget Sound is substantial. With over 40,000 data points, we will train a gradient boosted tree to be able to predict the probability of orcas being present in a designated zone. This information can be used to recommend commercial marine traffic to reduce speed in areas where there is a high probability of orcas being present. It has been shown in the past that these reductions in speed have an appreciable impact on marine noise pollution reduction. By making these speed reductions more targeted, it will reduce the impact on commercial vessel transits while also reducing the harmful noise pollution effects on orca populations.
      </p>

      <h2>Literature Review</h2>
      
      <h3>Applications of machine learning in animal behaviour studies (Valletta et al., 2017)</h3>
      <p>
        This review covers a variety of different approaches to applying machine learning in large data sets such as ours. Specifically, it capitalizes on the advantages of a hypothesis-free approach to modeling animal behavior. As the volume and complexity of data sets increase, it becomes more difficult to extract meaningful statistical analysis from the noise introduced in dimensionally complex data. Traditional approaches are not useful in scenarios such as this, and Valletta et al. (2017) have identified various methodologies where machine learning could be implemented instead. Specifically, they have identified improvements to be made in supervised learning, unsupervised learning, and feature selection, and how they apply to animal behavior.
      </p>
      <p>
        This specific paper will help identify the correct strategies and methodologies to implement with our specific dataset. This includes outlines for specific procedures for data exploration and feature extraction that will prove useful in preparing data to be fed to the model. It also references several other studies and how they approached machine learning. The approaches of other researchers can be used to help infer a new approach specific to our unique dataset.
      </p>

      <h3>Perspectives in machine learning for wildlife conservation (Tuia et al., 2022)</h3>
      <p>
        A pivotal question for this project is how this model will be used for marine mammal conservation. Generally, Tuia et al. (2022) cover these topics. They use perspectives from various disciplines to explore the implications of this nature of research and how to best leverage machine learning. They present a few examples of different data collection methods and how they can be utilized with machine learning. Finally, they capitalize on the importance of interdisciplinary cooperation between ecologists and computer scientists to help use machine learning to accelerate research and conservation efforts.
      </p>
      <p>
        This article has helped identify the strengths and shortcomings of our specific data set as well as the potential impact of the final product. It is critical to understand how the tools developed may be employed to help with conservation efforts. This will help guide the details of the implementation to best suit the desired use case. Additionally, it has highlighted the potential need to seek outside expertise on marine mammal behavior and how it might impact modeled behavior.
      </p>

      <h3>Animal behavior analysis methods using deep learning: A survey. Expert Systems with Applications (Fazzari et al., 2025)</h3>
      <p>
        This review assesses various use cases for machine learning, such as identifying animal behavior based on posture or observed movement patterns. It also assesses its uses in more traditional data sets such as GPS location data, camera detections, and other available data sets. It then further identifies the strengths of each dataset and the appropriate manipulations to it to extract useful data. It identifies the most commonly used approaches with those data sets and potential novel approaches that are likely to yield greater results.
      </p>
      <p>
        The review has been instrumental in identifying a specific model that could be employed with our dataset. Its straightforward breakdown of the efficacy of specific models and approaches for different types of desired outcomes presents a number of models that fit both the desired end results and use as input data sets like ours. It has also identified a number of optimizations that can be made to increase the accuracy of the end product.
      </p>

      <h2>Methods</h2>
      
      <h3>Scope:</h3>
      <p>
        Due to constraints in implementation, this article will focus primarily on the efficacy of machine learning models in predicting movement patterns of orca populations in the Puget Sound. The barrier in enacting regulatory frameworks to assess the model's efficacy as a tool to reduce marine noise pollution is too great; thus, we are limiting the assessment only to its predictive ability and not its utility as a tool.
      </p>
      <p>
        The data set we currently have access to only consists of reports inside the Puget Sound or the waters near Cape Flattery, extending to the San Juan Islands and the south Puget Sound to Olympia. This limits the area of our predictions only to those waters, as it is the primary concentration of our reports.
      </p>

      <h3>Approach:</h3>
      <p>
        The models will provide probabilities of orcas being present in one of the designated zones. It will do this based on real-time data and provide actionable reports that can be used to minimize impacts on orca populations in the Puget Sound. Real-time data will be provided via web-based reports, which will generate a new prediction.
      </p>
      <p>
        We will implement the model using the CRISP-DM methodology. CRISP-DM is a general methodology for developing models that we will adapt to our specific process.
      </p>

      <h4>Business Understanding:</h4>
      <p>
        The introductory paragraphs of this paper deal with understanding the requirements and use cases of this model. Most importantly, it is crucial that we start the process by identifying a specific business need to be addressed. In this case, we have identified that marine noise pollution has impacted the ecology and life cycle of orca populations in the Puget Sound. It is not only important to understand what the need is, but also to find tangible objectives that address this need. These are stated broadly in our goals(namely, as addressing the business need and reducing the impact of noise pollution) and specifically in our objectives, quantifying a specific metric to improve upon, such as the stated 40% reduction in marine noise pollution. We now tailor our deliverables to meet the criteria set forth by both the goals and the objectives, as well as obtain specifics from the end users on implementation and presentation.
      </p>

      <h4>Data Understanding:</h4>
      <p>
        We explored options for data sources and reached out to and gained consent from Orca Network. They are local to Puget Sound and are primarily focused on public conservation efforts. One of the services they offer is a public board where members may post text notifications that they have sighted a marine mammal. As part of assessing the data, we surveyed the percentage of reports that relate to orcas and found it to be roughly 80%. Of these reports, the majority were in populated areas and only provided the bare details of each sighting. Typically, there was no accurate count of the groups cited, and the only information that was reliable from post to post was the location and time. Locations were mostly referenced by geographic location rather than coordinates. The report quantity was determined to be fair. Orca network averaged 5673 reports a year between 2014 and 2023, culminating in 10920 in 2023. We determined that, given the quantity of data it was reasonable to expect to be able to generate a model provided the model were only to make predictions on the presence of orcas and not any other factors such as direction of travel, quantity or other behaviors as the accuracy of any information provided in these reports is dubious pertaining to any factor excluding location and time.
      </p>

      <h4>Data Preparation:</h4>
      <p>
        The data provided by the Orca network is in block text format. Each entry contains a header with the type of marine mammal, the location, and the time. None of the information provided in the reports is in a standardized format. Due to the large quantity of reports and the inconsistent nature of the formatting, it is impractical to employ traditional rational expressions to extract the data into a tabulated format. If time allowed, we would employ personnel to standardize the entries into a table, but that is not an option. As such, ChatGPT 4o API will be used to extract each entry from the block text, categorize it into one of the 25 standardized locations, and record the time and species in a table. Entries lacking enough information to positively identify any of the 3 fields will be discarded. In limited trials, ChatGPT 4o maintained a 97% accuracy, only incorrectly identifying 2 of 126 entries. This has been determined to be within the margin of error for our task. This methodology will be applied to all entries dating back to 2003 to obtain the final training dataset.
      </p>

      <h3>Implementation</h3>
      
      <h4>Model selection:</h4>
      <p>
        The data presents a classic classification issue. We will employ a gradient boosted tree, which will classify the probability of a sighting indicating orca presence in a zone. Each zone will use an individual binary classification model to identify the probability for that zone. This simplifies the approach and allows the individual models to specialize in identifying patterns inherent to that specific area rather than generalizations. Additionally, multiple sets of models will be trained for each zone to predict probabilities for different time frames. This is possible by still using the same dataset for each zone and shifting the test set window forward.
      </p>
      <p>
        Gradient boosted trees are lightweight and highly efficient compared to many other options. They can handle large data sets easily and tend not to consume too many resources. Decision trees tend to be optimized for data sets with fewer features and handle noise in data quite well. The greatest drawback with gradient boosted trees tends to be overfitting. If a smaller data set is used, the model can accidentally be tuned to features in the training data that are unique to the training data and don't represent a real case scenario. Because of the large size of our data set, we do not believe this will be a problem, but it can be mitigated if required. Specifically, the models being employed are XGBoost classifiers.
      </p>

      <h4>Dataset and feature selection:</h4>
      <p>
        The data is provided by Orca Network. They are a volunteer organization focusing on marine mammal conservation in the Puget Sound. One of the services they provide is allowing their members to make reports of whale sightings. These reports are made in text format via their website and often provide very little information. Typically, each report is a statement of the types of marine mammals spotted, location, time, and date. Historical records are presented as a block of text with each report in chronological order and grouped by month into separate web pages. Accuracy of the reports is typically validated by follow-up reports in the same area confirming the sighting. The format of each report is wildly inconsistent and provides little context beyond the sighting. Compiling this information is one of the primary tasks we will conduct to be able to leverage it.
      </p>
      <p>
        The Orca network has over 40,000 reports available. One of the dataset's primary advantages is the quantity of reports. The geographic distribution of reports is also a strong point. The Puget Sound is a fairly populous area, and as such, reports are consistently made even in more rural areas. This helps to ensure that not as much reporting bias plays a role in our data, skewing our probabilities to areas with a greater population (this may still be a concern). The reports span a period of over 20 years and, as such, demonstrate a wide variety of seasonal information that can be used to help identify seasonal trends.
      </p>
      <p>
        Unfortunately, the limitations of the data are extensive. The nonstandard nature of the reports leads to a broad variety of terms used to refer to similar areas, meaning that exactly pinpointing the area a sighting was reported in is difficult. Furthermore, report locations are often made as the location of the report being the location of the reporter and not the marine mammal, further confounding the issue. Similar issues arise with a variety of synonyms being used to describe the same species, and some reports are made with specific specimen identifier numbers rather than a general species. The only consistent field is the date and time, as those are standardized by the time the report was submitted.
      </p>
      <p>
        Given the sheer volume of reports and the limited scope of the project, tabulating reports manually is not possible. Initial intake of the data will be done by the GPT-5 API. The API will be instructed to take blocks of text and return reports in a tabulated form with satirized entries for each column. It will return reports in the sequence it ingests them and return them with a sequential ID number associated with them. GPT-5 will be instructed to remove any data that does not have enough information to generate a report. Additionally, we will flag any reports that are not in chronological order as listed in the source to help identify outliers in the data time segment. Both of these actions will help verify the validity of GPT-5's parsing of the data and ensure the majority of errors are caught and that the dataset is clean. GPT-5 displayed a 98% accuracy on a sample size of one month. Once the corrupted data has been removed, the base information will be transferred into the final table, and during this transfer, we will conduct feature engineering to extract metrics that the model can reason on.
      </p>
      <p>
        Once we have done the base data extraction, it is time to engineer the feature set to optimize for model predictions. To do this, we will standardize data into set groups and break down complex strings into base components that represent possible factors that could influence the results.
      </p>
      <p>
        The first example of that in this data set is breaking down the date and time field into separate fields that present the information at a fundamental level. The date time field is broken down into 4 fields that each could represent a different aspect of the data. The month will help the model distinguish between seasonal changes in the movements of orcas. The hour field will help correct for potential report density depending on the time of day, as well as potential differences in activity. The sun up field is meant to have a similar effect as the hour field, but will account for seasonal changes in daylight. The day of the week is also intended to help mitigate changes in report density that may occur due to a higher volume of potential reporters at different times of the week.
      </p>
      <p>
        We will conduct a similar process with report quantities in attempting to convey different factors that the data could represent. We will calculate with a SQL query the number of reports in the same zone in the last 5 hours. This will help convey if orcas have been loitering in the same zone for an extended period of time or if they are fairly stationary. Next are the nearby reports. This is the sum of reports in the last 5 hours in the zones immediately adjacent to this zone. This methodology will also be used to calculate the number of reports in the second-degree neighbor as well. This adjacency calculation will hopefully give the models geospatial insight into the orca movement patterns. If orcas have been frequenting areas near this one, it will increase the chances they may transit into this zone. Finally, we will include a tally of all reports in this zone in the last 24 hours. This is meant to help predict short-term trends that may show a group of orcas has been consistently visiting this area over the last day.
      </p>
      <p>
        A later assessment of our approach also indicated that an engineered absence report may also be useful in the discrimination of reports. We used a relatively simple approach to generating absence reports.
      </p>
      <p>
        Determine eligible zones:
        <ul>
          <li>No sightings in this zone in the last 2 hours</li>
          <li>No sightings in any adjacent zone in the last 3 hours</li>
          <li>No absence reports already in this zone in the last 3 hours</li>
        </ul>
      </p>
      <p>
        Once the absence reports we generated, we employed a weighted down sampling technique described in Weighted Random Sampling (Efraimidis & Spirakis, 2005). The weights were determined by seasonal averages for reports for that zone and an effort assessment, that is, the average of reports by hour for that zone.
      </p>

      <h3>Iterations</h3>
      <p>
        The initial approach used 3 large 16-hour time windows and a general classification model for all zones from the SKLearn library for Python. The approach was not well-suited to the dataset and yielded minimal results. This model also did not benefit from the absence reports that help provide negative signaling to the model.
      </p>
      
      <div style={{ textAlign: 'center', margin: '20px 0' }}>
        <img src={figure1} alt="Figure 1" style={{ maxWidth: '100%', height: 'auto' }} />
        <p><strong>Figure 1.</strong></p>
      </div>
      
      <p>
        The AUC of this model was considered unsatisfactory (see Figure 1), and it was unable to generate any usable predictions. At the time, a change in model was assessed to be appropriate to see if any appreciable changes could be seen without any further alterations in approach. This was the point at which the XGBoost classifier was implemented. Initially, it used the same multi-classification approach and large time buckets. The only primary change was the model. Results yielded vary similarly to the original model (see figure 2) with a very low AUC, providing statistically insignificant predictions.
      </p>
      <p>
        The continued poor results indicated that a fundamental change in approach was called for. After reassessing the objectives, we decided to shift the time window segments down to 6 hours and change our technical approach as well. It was decided that, in addition to the reports, a form of negative signaling would be helpful for the model to identify patterns of avoidance as well. This led to the development of the absence reports as an attempt to also identify these avoidance patterns. Additionally, it was identified that designating individual classifiers for each zone would help the model identify zone-specific movement patterns. With a 1 to 3 ratio of real sightings to the generated absences, we have over 180 thousand datapoints. It was judged that a dataset of this size would be adequate to train a specific model for each zone without any adverse impacts.
      </p>
      
      <div style={{ textAlign: 'center', margin: '20px 0' }}>
        <img src={figure2} alt="Figure 2" style={{ maxWidth: '100%', height: 'auto' }} />
        <p><strong>Figure 2</strong></p>
      </div>

      <h2>Analysis</h2>
      <p>
        The iterative development of the model led to a fairly good predictive model.
      </p>
      
      <div style={{ textAlign: 'center', margin: '20px 0' }}>
        <img src={figure3} alt="Figure 3" style={{ maxWidth: '100%', height: 'auto' }} />
        <p><strong>Figure 3</strong></p>
      </div>
      
      <div style={{ textAlign: 'center', margin: '20px 0' }}>
        <img src={figure41} alt="Figure 4.1" style={{ maxWidth: '100%', height: 'auto' }} />
        <p><strong>Figure 4.1</strong></p>
      </div>
      
      <div style={{ textAlign: 'center', margin: '20px 0' }}>
        <img src={figure42} alt="Figure 4.2" style={{ maxWidth: '100%', height: 'auto' }} />
        <p><strong>Figure 4.2</strong></p>
      </div>
      
      <div style={{ textAlign: 'center', margin: '20px 0' }}>
        <img src={figure43} alt="Figure 4.3" style={{ maxWidth: '100%', height: 'auto' }} />
        <p><strong>Figure 4.3</strong></p>
      </div>

      <p>
        Model metrics indicate that the model excels at accurately identifying positive sightings in the designated zones. With an average AUC of .856 across all models and zones, this indicates that the model consistently identifies positive cases. Unfortunately, the accuracy of the model is the primary issue (See figures 4.1-4.3). Except in predictions of high confidence, such as seen in the extremes of the calibration plot, the model fails to accurately capture absences. This is further enforced by the confusion matrix (see Figure 5). The confusion matrix indicates that for the 0-6 hour bucket, the model predicts 3 times more sightings than actually occur. Despite that, it does a fairly good job at not failing to predict a sighting when there is one. This is overall indicative of the data set and the engineered features. Out of possible miscalibrations in this scenario, the cost of a false negative is higher than a false positive, meaning that despite the flaws in the model, its predictions are still of value.
      </p>
      
      <div style={{ textAlign: 'center', margin: '20px 0' }}>
        <img src={figure5} alt="Figure 5" style={{ maxWidth: '100%', height: 'auto' }} />
        <p><strong>Figure 5</strong></p>
      </div>

      <h3>Discussion</h3>
      
      <h4>Practical considerations:</h4>
      <p>
        Generally, the approach used resulted in a usable model. One issue identified after implementation was the frequency of new data. Currently, the model uses an Email inbox to receive new reports. Unfortunately, the emails are only sent on a weekly basis, and as such, the predictions are often dated and are of little use. Additionally, the continuity of reports provided in the emails is also an issue. Often, a couple of days of data are missing between reports. This would be a primary area for improvement. It would be possible to instead pull reports from the Orca Network Facebook page, which is updated with near-live information. This information is identical to the reports provided in the emails. Having the most recent data is imperative for its function as an early warning system, but it had no effect on our statistical assessments of the model.
      </p>

      <h4>Potential model changes:</h4>
      <p>
        The low accuracy is a concerning characteristic of the current model. We believe this is probably due to the ratio of absence reports generated. A more conservative approach of a 1:1 ratio would probably yield better results, although this would require further study to validate. If given more resources and time, a full re-parsing of the raw data would also probably benefit the outcome. This would include reworking the zones used and better defining boundaries. We believe that under 5% of reports were incorrectly transcribed, but if this could be corrected to an even lower amount, the model would benefit.
      </p>
      <p>
        Once a successful approach was identified with our current model, very little time was taken to further optimize results. I theorize that, given more time, the model could be fine-tuned with the current data set to double accuracy and increase AUC to at or near .90. The primary limiting factor in this study was time.
      </p>

      <h4>Expanded datasets:</h4>
      <p>
        Additional data sources could also be integrated with the current one. The primary issue would be that the older elements in the current data set would have to be discarded. The model would not handle training well if the additional data set were integrated in the middle chronologically with the old data set.
      </p>

      <h4>Implications for further areas of study:</h4>
      <p>
        While it is evident that in the limited area of the Puget Sound it is possible to track orca movements, this application may not transfer well to other geographic areas. We believe that part of the reason the model is able to predict movement patterns is the geographic constraints in place in the Puget Sound. The diverse islands present the navigable waters more as bounded waterways than as an open ocean. As such, the potential paths presented to orcas are limited inside the Puget Sound. The bounding caused by the islands also presents a much higher opportunity for sightings compared to areas of open coast and coastal waters. Further study would be required to see if this method has any application in near-coastal waters and the open ocean.
      </p>

      <h2>Conclusion</h2>
      
      <h3>Limitations</h3>
      <p>
        The limited scope of this project has restricted the evaluation of the hypothesis to only the utility of the model in predicting orca movements in a manner that would be insightful to professional mariners. Provided the efficacy of the models, further study would need to be conducted on methodologies, applications, and impacts for marine mammal conservation.
      </p>

      <h3>Implications for the hypotheses</h3>
      <p>
        Analysis of the models displayed a mean AUC (Area under the curve) of 0.856. By most standards, this is considered good to excellent discriminatory ability and surpasses almost all benchmarks for what is considered a useful insight. In the limited scope of the Puget Sound, it is evident that with the high volume of reports available spanning a diverse period, it is possible to predict Orca movement patterns with some measure of accuracy.
      </p>

      <h2>Sources:</h2>
      <p>
        Scott, M., & Mayer, T. (2023). International trade, noise pollution, and killer whales. https://www.nber.org/system/files/working_papers/w31390/w31390.pdf
      </p>
      <p>
        Valletta, J. J., Torney, C., Kings, M., Thornton, A., & Madden, J. (2017). Applications of machine learning in animal behaviour studies. Animal Behaviour, 124, 203–220. https://doi.org/10.1016/j.anbehav.2016.12.005
      </p>
      <p>
        Tuia, D., Kellenberger, B., Beery, S., Costelloe, B. R., Zuffi, S., Risse, B., Mathis, A., Mathis, M. W., van Langevelde, F., Burghardt, T., Kays, R., Klinck, H., Wikelski, M., Couzin, I. D., van Horn, G., Crofoot, M. C., Stewart, C. V., & Berger-Wolf, T. (2022). Perspectives in machine learning for wildlife conservation. Nature Communications, 13(1). https://doi.org/10.1038/s41467-022-27980-y
      </p>
      <p>
        Fazzari, E., Romano, D., Falchi, F., & Stefanini, C. (2025). Animal behavior analysis methods using deep learning: A survey. Expert Systems with Applications, 289, 128330. https://doi.org/10.1016/j.eswa.2025.128330
      </p>
      <p>
        Weighted Random Sampling; Efraimidis, Spirakis. (2005). SpringerReference. https://doi.org/10.1007/springerreference_57997
      </p>
      <p>
        Orca Network. (n.d.). Orca Network. https://www.orcanetwork.org/
      </p>
      <p>
        (Source for dataset)*
      </p>
      </div>
    </div>
  );
};

export default TechnicalSummaryPage;
