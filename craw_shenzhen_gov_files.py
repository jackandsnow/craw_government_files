import os

from lxml import etree

from common.tools import get_url_text, get_total_page_num


class CrawShenZhenGov:

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

    def get_info_urls_in_each_page(self, url):
        """
        爬取每个网页上通知文件的链接
        :param url: target url
        :return: info_urls list
        """
        page_content = get_url_text(url)
        html = etree.HTML(page_content)
        urls = html.xpath('//div[@class="zx_ml_list"]/ul/li/div/a/@href')
        urls = list(map(lambda x: 'http://www.sz.gov.cn' + x.split('..')[-1] if 'http' not in x else '', urls))
        return urls

    def get_basic_info(self, base_infos):
        """
        拼接所有的基础信息到一个列表中
        :param base_infos: [['索引号'], ['分类']， ['发布机构'], ['发布日期'], ['名称'], ['文号']， ['主题词']]
        :return: ['索引号', '分类'， '发布机构', '发布日期', '名称', '文号'， '主题词']
        """
        infos = []
        for info in base_infos:
            if len(info) > 0:
                infos.extend(info)
            else:
                infos.extend(' ')
        return infos

    def get_notification_infos(self, url):
        """
        在通知文件页面爬取通知的内容
        :param url: info url
        :return: base_infos， content
        """
        page_content = get_url_text(url)
        html = etree.HTML(page_content)
        # ['索引号', '分类'， '发布机构', '发布日期', '名称', '文号'， '主题词']
        index = html.xpath('//div[@class="xx_con"]/p[1]/text()')
        aspect = html.xpath('//div[@class="xx_con"]/p[2]/text()')
        announced_by = html.xpath('//div[@class="xx_con"]/p[3]/text()')
        announced_date = html.xpath('//div[@class="xx_con"]/p[4]/text()')
        title = html.xpath('//div[@class="xx_con"]/p[5]/text()')
        document_num = html.xpath('//div[@class="xx_con"]/p[6]/text()')
        key_word = html.xpath('//div[@class="xx_con"]/p[7]/text()')
        base_infos = [index, aspect, announced_by, announced_date, title, document_num, key_word]
        base_infos = self.get_basic_info(base_infos)
        # print('This is basic info: ', base_infos)
        paragraphs = html.xpath('//div[@class="news_cont_d_wrap"]//p/text()')  # 文件内容信息
        if len(paragraphs) == 0:  # 某些页面结构特殊
            paragraphs = html.xpath('//div[@class="news_cont_d_wrap"]//div/text()')  # 文件内容信息
        contents = '\n'.join(paragraphs)
        # print(contents)
        return base_infos, contents

    def write_notification_to_txt(self, save_dir, url, base_infos, contents):
        """
        保存通知的详细信息到文本文件
        :param save_dir: 保存的路径
        :param url: 通知url
        :param base_infos: 通知的基本信息（'索引号', '分类'， '发布机构', '发布日期', '名称', '文号'， '主题词'）
        :param contents: 通知内容
        :return: None
        """
        # print(base_infos)
        filename = '%s/%s.txt' % (save_dir, base_infos[4].replace('/', '-'))
        with open(filename, 'w', encoding="utf-8") as f:
            f.write(url + '\n')
            f.write('索引号: %s\n' % base_infos[0])
            f.write('信息分类: %s\n' % base_infos[1])
            f.write('发布机构: %s\n' % base_infos[2])
            f.write('发布日期: %s\n' % base_infos[3])
            f.write('信息名称: %s\n' % base_infos[4])
            f.write('文   号: %s\n' % base_infos[5])
            f.write('关键词: %s\n\n' % base_infos[6])
            f.write(contents)
        f.close()

    def run(self, save_dir, target_url):
        """
        主程序运行的入口
        :param save_dir: 保存文本的目录
        :param target_url: 要爬取的home url
        :return: None
        """
        # 以下三个需要根据网页的 html 结构来设置
        prefix = 'createPageHTML('
        suffix = ');</script>'
        delimiter = ','
        num = get_total_page_num(target_url, prefix, suffix, delimiter)
        page_urls = self.get_all_pages_urls(target_url, num)
        for page_url in page_urls:
            info_urls = self.get_info_urls_in_each_page(page_url)
            for info_url in info_urls:
                print('Get Information From ', info_url)
                if '' != info_urls:
                    base_infos, contents = self.get_notification_infos(info_url)
                    # 剔除掉没有爬到内容的通知
                    if contents.strip() != '':
                        self.write_notification_to_txt(save_dir, info_url, base_infos, contents)


if __name__ == '__main__':

    gov = CrawShenZhenGov()
    save_dirs = ['data/shenzhen/gov_files', 'data/shenzhen/office_files']
    target_urls = ['http://www.sz.gov.cn/zfwj/zfwjnew/szfwj_139223/index.htm',
                   'http://www.sz.gov.cn/zfwj/zfwjnew/szfbgtwj_139225/index.htm']

    for i in range(0, len(target_urls)):
        if os.path.exists(save_dirs[i]) is False:
            os.mkdir(save_dirs[i])
        gov.run(save_dirs[i], target_urls[i])

    # gov.get_notification_infos('http://www.sz.gov.cn/zfgb/2007/gb575/200810/t20081019_94087.htm')
    print('*************** Program Finished *****************')
