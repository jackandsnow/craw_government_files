# craw_government_files

This project aims to crawl the public files of different governments of cities, like public government files, public office files, police files, etc.

1.Environment Introduction: This project is implemented by **python 3**, and the dependencies you need to install are mainly **pandas**, **openpyxl**, **docx**, **requests** and **lxml**.

2.Codes Introduction: The file named *'common.tools.py'* provides some **common functions** for you to craw files from different governments' websites.
For example, These functions can help you get the html text from a target url, help you get the total page number of notifications for each website, help you download files through a link, help you write word or excel files.

3.File Storage: The files crawled from one government website can be saved as **word files**, and the attachments will be downloaded as well. what's more, all files detail information will be written to an excel file. (Also, you can just save the files to **txt file**, seeing the following picture.)

![files.PNG](https://github.com/jackandsnow/craw_government_files/raw/master/images/files.PNG)

4.Examples: This project is only for crawling Shenzhen government public files. As you can see in codes, different python files for crawling different public files.
For instance, the file *'craw_shenzhen_gov_files.py'* is to *crawl files of Shenzhen government*. The file *'craw_shenzhen_gov_bulletin.py'* aims to *crawl bulletins of Shenzhen government*.

5.If you just want to crawl other governments' files, you just need to change the target urls and adjust the codes according to its website structure. I hope this project can help more companions who want to learn about crawling.
Finally, if you are really benefited from this project, please give a star for this project.
