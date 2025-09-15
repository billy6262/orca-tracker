# About This Project

This Orca Tracker application serves as my Computer Science capstone project, demonstrating the practical application of machine learning techniques in marine mammal conservation. The project showcases:

- Advanced data processing and analysis of over 40,000 marine mammal sighting reports
- Implementation of XGBoost machine learning models for predictive analytics
- Full-stack web development with React frontend and Django backend
- Real-world application addressing marine conservation challenges
- Integration of maritime industry knowledge with computer science principles

## C. Design and develop your fully functional data product that addresses your identified business problem or organizational need from part A. Include each of the following attributes, as they are the minimum required elements for the product:

- one descriptive method and one nondescriptive (predictive or prescriptive) method

Methods are located on the charts, map, and reports pages of the web application.

- collected or available datasets

Raw data is located in the pre-prod folder, and a copy of the production dataset is located in the primary folder.

- decision support functionality

Evident in the web application.

- ability to support featurizing, parsing, cleaning, and wrangling datasets

This functionality is embedded in the Django back-end.

- methods and algorithms supporting data exploration and preparation

This is evident in the web application. Additionally, in the pre-prod folder under model training is a Jupyter notebook labeled Data Exploration with the imported dataset. (The Docker container for the DB must be online and locally hosted to import the data. For dependencies, use VSCode and the virtual environment package in the .venv folder of the main directory. This method was not primarily utilized but is available for further exploration.)

- data visualization functionalities for data exploration and inspection

This is evident in the web application.

- implementation of interactive queries

The Django admin page is available when locally hosted via http://localhost:8000/admin/. For security, this page is not available for the web-hosted version. (The Docker containers must be running to access this page.)
Additionally, SQL queries may be directed to the server when locally hosted or the API is available via http://localhost:8000/api/docs/.

- implementation of machine-learning methods and algorithms

This functionality is implemented in the Django backend.

- functionalities to evaluate the accuracy of the data product

In the pre-prod folder under the model_training folder is the model metrics visualization module. This can be used to generate accuracy metrics when the model is trained. All the metrics in the technical implementation document were generated with this module. (The Docker container for the DB must be online to import the data. For dependencies, use VSCode and the virtual environment package in the .venv folder of the main directory. This method was not primarily utilized but is available for further exploration.)

- industry-appropriate security features

The web-hosted version supports SSL, and the api only presents GET methods to minimize public interaction.

- tools to monitor and maintain the product

The Django admin page is available when locally hosted via http://localhost:8000/admin/. For security, this page is not available for the web-hosted version. (The Docker containers must be running to access this page.)

- a user-friendly, functional dashboard that includes three visualization types

This is evident in the web application.

## D. Create each of the following forms of documentation for the product you have developed:

- a business vision or business requirements document

Attached with submission.

- raw and cleaned datasets with the code and executable files used to scrape and clean data (if applicable)

Raw data is located in the pre-prod folder, and a copy of the production dataset is located in the primary folder. Copies of the SQL featurizing scripts are located in the pre-prod folder under SQL functions-data-fetcher. The Django backend data_pipeline module is responsible for ingesting the raw data.

- code used to perform the analysis of the data and construct a descriptive, predictive, or prescriptive data product

The scripts used for model training are constrained in the pre-prod folder under model training.

- assessment of the hypotheses for acceptance or rejection

Attached with submission. C964 approach Implementation and review Task D.

- visualizations and elements of effective storytelling supporting the data exploration and preparation, data analysis, and data summary, including the phenomenon and its detection

Attached with submission. C964 approach Implementation and review Task D.

- assessment of the product’s accuracy

Attached with submission. C964 approach Implementation and review Task D.

- the results from the data product testing, revisions, and optimization based on the provided plans, including screenshots

Attached with submission. C964 approach Implementation and review Task D.

- source code and executable file(s)
  too large to attach as a single file.
  https://github.com/billy6262/orca-tracker

- a quick-start guide summarizing the steps necessary to install and use the product

Attached with submission.
