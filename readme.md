# craw_government_files

This project aims to crawl the public files of different cities' government, like public government files, public office files, etc.

1.Environment Introduction: This project is implemented by **python 3**, and the dependencies are mainly **requests** and **lxml**.

2.Codes Introduction: The file named *'common.tools.py'* provides some **common functions** for you to craw files from different governments' websites.
The function named *'get_url_text()'* helps tp get the html text from a target url and the *'get_total_page_num()'* function helps to get the total page number of notifications for each website.

3.File Storage: The files crawled from one government website are saved as **TXT file** as you can see in the following picture. And the filenames are consistent with the names of notifications.

![files.PNG](https://github.com/jackandsnow/craw_government_files/raw/master/images/files.PNG)

4.Examples: Here is an example in the *'craw_shenzhen_gov_files.py'* file, which is to *crawl files of Shenzhen government*. You just need to change the example file to crawl another government files according to its website structure.
And maybe in the future, the author will provide more examples so that you can star this project for update.
