# Code-of-Science-in-Wikipedia-
This repository offers the code we used in the project *Science in Wikipedia*.

Please find the code in the file *Code*, in this file, we list 4 fiels as below:

1. [Input and read the dataset](Code/Input_and_read_the_dataset.py): Read the *Wikipedia Citations* dataset.

    1. Download the [Wikipedia Citations dataset **minimal**](https://github.com/Harshdeep1996/cite-classifications-wiki) and store it in the folder and name it as "minimal_dataset.parquet".
    
    2. Execute script
    
    3. The result will be *"page_doi.parquet"* which includes wikipedia page title and corresponding doi. This will be used in step 2,3,4.

2. [Extracting data from Dimensions](Code/Extracting_data_from_Dimensions.py): Extract data from Dimensions.

    1.Read the documents fo [Dimensions API](https://docs.dimensions.ai/dsl/api.html) and apply for your own account.


    2.Replace your key follow the note and execute script.


    3.The result is "result_dimension.parquet", which offers the fields, dois, journal, open_access, recent_citations, research_org_countries, times_cited, types and year of             journal articles. It will be used in step 4.
    
    
3. [Adding topic from Wikipedia API](Code/Adding_topic_from_Wikipedia_API.py): Add ORES topics from Wikipedia API.
 
    1.Use the [topic api](https://wiki-topic.toolforge.org//topic) to get wikipedia page topics.
    
    2.The result is "page_topic.parquet" and it will be used in step 4.
    
4. [Analysis and figures](Code/Analysis_and_figures.py): Replicate the analysis from the paper, including the main figures.

    1. Read all three documents above and intergrate it follow the note.
    2. Create co-citation network and Bibliographic coupling network, and then use leiden algorithm to detect the community and create the super network.
    3. Integrate supporting datasets to networks (ORES, WikiProjects, FoR) 
    4. Follow the note to re-do the main Figures in the paper.
