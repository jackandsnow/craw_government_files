import os

from lxml import etree

from common.tools import get_html_text, get_total_page_num, download_file, write_word_file, write_excel_file


class CrawShenZhenNews:

    def get_all_pages_urls(self, url, page_num):
        """
        根据 page number，拼接出所有页数的 url
        :param url: target url
        :param page_num: page number
        :return: page_urls list
        """
        urls = [url]  # add first page url
        url_pre = url.replace('.htm', '')
        for i in range(1, page_num):
            full_url = '%s_%s.htm' % (url_pre, i)
            urls.append(full_url)
        return urls

    def get_info_urls_of_news(self, url):
        """
        爬取新闻发布网页上通知文件的链接
        :param url: target url
        :return: info_urls list, titles list
        """
        page_content = get_html_text(url)
        html = etree.HTML(page_content)
        urls = html.xpath('//div[@class="zx_ml_list"]/ul/li/span[@class="tit"]/a/@href')
        titles = html.xpath('//div[@class="zx_ml_list"]/ul/li/span[@class="tit"]/a//text()')
        urls = list(map(
            lambda x: url.split('index')[0] + x.split('./')[-1] if 'http' not in x else x,
            urls))
        return urls, titles

    def get_notification_infos(self, url):
        """
        在通知文件页面爬取通知的内容
        :param url: info url
        :return: content
        """
        page_content = get_html_text(url)
        if not page_content:
            return ''
        html = etree.HTML(page_content)
        paragraphs = html.xpath('//div[@class="TRS_Editor"]//p')  # 段落信息
        contents = []
        for paragraph in paragraphs:
            contents.append(paragraph.xpath('string(.)').strip())
        contents = '\n'.join(contents)
        # print(contents)
        return contents

    def write_notification_to_docx(self, save_dir, title, contents):
        """
        保存通知的详细信息到word文件
        :param save_dir: 保存的路径
        :param title: 通知标题
        :param contents: 通知内容
        :return: None
        """
        title = title.replace('/', '-').replace('\\', '-').replace(' ', '') \
            .replace('<', '(').replace('>', ')').replace('"', '-')
        # 处理文件名过长
        filename = save_dir + '/' + title + '.docx'
        filename = save_dir + '/...' + title[-50:] + '.docx' if len(filename) > 180 else filename
        # 写入word文档
        write_word_file(filename=filename,
                        title=title, data_list=[contents])

    def run(self, save_dir, target_url):
        """
        主程序运行的入口
        :param save_dir: 保存文本的目录
        :param target_url: 要爬取的home url
        :return: None
        """
        # 以下三个需要根据网页的 html 结构来设置
        prefix = 'createPageHTML('
        suffix = ');'
        delimiter = ','
        num = get_total_page_num(target_url, prefix, suffix, delimiter)
        page_urls = self.get_all_pages_urls(target_url, num)
        for page_url in page_urls:
            info_urls, info_titles = self.get_info_urls_of_news(page_url)  # 新闻发布
            for k in range(len(info_urls)):
                print('Get Information From ', info_urls[k])
                if '' != info_urls[k]:
                    contents = self.get_notification_infos(info_urls[k])
                    # 剔除掉没有爬到内容的通知
                    if contents.strip() != '':
                        self.write_notification_to_docx(save_dir, info_titles[k], contents)
        print('Write', save_dir.split('data/')[-1], 'Finished!\n')


if __name__ == '__main__':
    news = CrawShenZhenNews()

    # 新闻发布
    save_dirs = [
        'data/新闻发布/新闻发布稿',
        'data/新闻发布/采访通知',
        'data/新闻发布/媒体关注',
        'data/新闻发布/往期回顾'
    ]
    target_urls = [
        'http://www.sz.gov.cn/cn/xxgk/xwfyr/xwtg/index.htm',
        'http://www.sz.gov.cn/cn/xxgk/xwfyr/tzgg/index.htm',
        'http://www.sz.gov.cn/cn/xxgk/xwfyr/mtgz/index.htm',
        'http://www.sz.gov.cn/cn/xxgk/xwfyr/wqhg/index.htm'
    ]

    for i in range(0, len(target_urls)):
        if os.path.exists(save_dirs[i]) is False:
            os.mkdir(save_dirs[i])
        news.run(save_dir=save_dirs[i],
                 target_url=target_urls[i])

    print('*************** Program Finished *****************')
