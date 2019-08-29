import os

from lxml import etree

from common.tools import get_html_text, get_total_page_num, download_file, write_word_file, write_excel_file


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

    def get_info_urls_of_public(self, url):
        """
        爬取政府文件网页上通知文件的链接
        :param url: target url
        :return: info_urls list
        """
        page_content = get_html_text(url)
        html = etree.HTML(page_content)
        urls = html.xpath('//div[@class="zx_ml_list"]/ul/li/div/a/@href')
        urls = list(map(lambda x: 'http://www.sz.gov.cn' + x.split('..')[-1] if 'http' not in x else x, urls))
        return urls

    def get_info_urls_of_policy(self, url):
        """
        爬取政策解读网页上通知文件的链接
        :param url: target url
        :return: info_urls list
        """
        page_content = get_html_text(url)
        html = etree.HTML(page_content)
        script_list = html.xpath('//div[@class="zx_ml_list"]/ul/li/div/script/text()')
        # get url from script_list, like "var _url = './201907/t20190708_18040234.htm';"
        urls = list(map(
            lambda s: 'http://www.sz.gov.cn/cn/xxgk/zfxxgj/zcjd' + s.split('var _url = \'.')[-1].split('\';')[0],
            script_list))
        return urls

    def get_notification_infos(self, url):
        """
        在通知文件页面爬取通知的内容
        :param url: info url
        :return: base_infos， content
        """
        page_content = get_html_text(url)
        html = etree.HTML(page_content)
        # ['索引号', '省份', '城市', '文件类型', '文号', '发布机构', '发布日期', '标题', '主题词']
        index = html.xpath('//div[@class="xx_con"]/p[1]/text()')
        aspect = html.xpath('//div[@class="xx_con"]/p[2]/text()')
        announced_by = html.xpath('//div[@class="xx_con"]/p[3]/text()')
        announced_date = html.xpath('//div[@class="xx_con"]/p[4]/text()')
        title = html.xpath('//div[@class="xx_con"]/p[5]/text()')
        document_num = html.xpath('//div[@class="xx_con"]/p[6]/text()')
        key_word = html.xpath('//div[@class="xx_con"]/p[7]/text()')
        base_infos = [index, ['广东省'], ['深圳市'], aspect, document_num, announced_by, announced_date, title, key_word]
        # encode是为了保存Excel，否则出错
        base_infos = list(map(lambda x: x[0].encode('utf-8') if len(x) > 0 else ' ', base_infos))
        # print('This is basic info: ', base_infos)
        paragraphs = html.xpath('//div[@class="news_cont_d_wrap"]//p')  # 段落信息
        contents = []
        for paragraph in paragraphs:
            contents.append(paragraph.xpath('string(.)').strip())
        contents = '\n'.join(contents)
        # deal with attachments
        attachments = []
        script_str = html.xpath('//div[@class="fjdown"]/script/text()')[0]
        # if there are attachments, then get attachments from script
        if script_str.find('var linkdesc="";') == -1:
            attach_names = script_str.split('var linkdesc="')[-1].split('";')[0].split(';')
            attach_urls = script_str.split('var linkurl="')[-1].split('";')[0].split(';')
            suffix = url.split('/')[-1]
            for k in range(len(attach_urls)):
                attach_url = url.replace(suffix, attach_urls[k].split('./')[-1])
                attach_name = attach_names[k].replace('/', '-').replace('<', '(').replace('>', ')')
                # print(attach_name, attach_url)
                attachments.append([attach_name, attach_url])
        # print(contents)
        return base_infos, contents, attachments

    def write_notification_to_docx(self, save_dir, base_infos, contents, attachments):
        """
        保存通知的详细信息到word文件
        :param save_dir: 保存的路径
        :param base_infos: 通知的基本信息（'索引号', '省份', '城市', '文件类型', '文号', '发布机构', '发布日期', '标题', '主题词'）
        :param contents: 通知内容
        :param attachments: 附件信息
        :return: None
        """
        title = bytes.decode(base_infos[-2]).replace('/', '-').replace(' ', '') \
            .replace('<', '(').replace('>', ')').replace('"', '-')
        # 下载附件
        if len(attachments) > 0:
            # 有附件则要新建目录
            save_dir = save_dir + '/' + title
            os.mkdir(save_dir)
            for attachment in attachments:
                suffix = attachment[1].split('.')[-1]
                attach_name = attachment[0] + '.' + suffix if suffix not in attachment[0] else attachment[0]
                # 不下载mp4视频
                if suffix != 'mp4':
                    download_file(file_url=attachment[1], filename=save_dir + '/' + attach_name)
        # 处理文件名过长
        filename = save_dir + '/' + title + '.docx'
        filename = save_dir + '/...' + title[-50:] + '.docx' if len(filename) > 180 else filename
        # 写入word文档
        write_word_file(filename=filename,
                        title=title, data_list=[contents])

    def run(self, excel_name, sheet_name, save_dir, target_url):
        """
        主程序运行的入口
        :param excel_name: 保存的Excel表名
        :param sheet_name: 保存的Excel表sheet名
        :param save_dir: 保存文本的目录
        :param target_url: 要爬取的home url
        :return: None
        """
        base_info_list = []
        # 以下三个需要根据网页的 html 结构来设置
        prefix = 'createPageHTML('
        suffix = ');'
        delimiter = ','
        num = get_total_page_num(target_url, prefix, suffix, delimiter)
        page_urls = self.get_all_pages_urls(target_url, num)
        for page_url in page_urls:
            # info_urls = self.get_info_urls_of_public(page_url)    # 政府文件用
            info_urls = self.get_info_urls_of_policy(page_url)  # 政策解读用
            for info_url in info_urls:
                print('Get Information From ', info_url)
                if '' != info_url:
                    base_infos, contents, attachments = self.get_notification_infos(info_url)
                    # 剔除掉没有爬到内容的通知
                    if contents.strip() != '':
                        self.write_notification_to_docx(save_dir, base_infos, contents, attachments)
                        base_info_list.append(base_infos)
        # 写入信息到Excel
        if len(base_info_list) > 0:
            columns = ['索引号', '省份', '城市', '文件类型', '文号', '发布机构', '发布日期', '标题', '主题词']
            write_excel_file(filename=excel_name, data_list=base_info_list,
                             sheet_name=sheet_name, columns=columns)
            print('Write', sheet_name, 'Finished!\n')


if __name__ == '__main__':
    gov = CrawShenZhenGov()

    # 政府文件
    # save_dirs = [
    #     'data/政府文件/市政府令',
    #     'data/政府文件/市政府文件',
    #     'data/政府文件/市政府函',
    #     'data/政府文件/市政府办公厅文件',
    #     'data/政府文件/市政府办公厅函',
    #     'data/政府文件/部门规范性文件'
    # ]
    # target_urls = [
    #     'http://www.sz.gov.cn/zfwj/zfwjnew/szfl_139222/index.htm',
    #     'http://www.sz.gov.cn/zfwj/zfwjnew/szfwj_139223/index.htm',
    #     'http://www.sz.gov.cn/zfwj/zfwjnew/szfh_139224/index.htm',
    #     'http://www.sz.gov.cn/zfwj/zfwjnew/szfbgtwj_139225/index.htm',
    #     'http://www.sz.gov.cn/zfwj/zfwjnew/szfbgth_139226/index.htm',
    #     'http://www.sz.gov.cn/zfwj/zfwjnew/bmgfxwjnew/index.htm'
    # ]

    # 政策解读
    save_dirs = [
        'data/政策解读'
    ]
    target_urls = [
        'http://www.sz.gov.cn/cn/xxgk/zfxxgj/zcjd/index_wzjd_42052.htm'
    ]

    for i in range(0, len(target_urls)):
        if os.path.exists(save_dirs[i]) is False:
            os.mkdir(save_dirs[i])
        sheet_name = save_dirs[i].split('data/')[-1].replace('/', '_')
        gov.run(excel_name='data/深圳市.xlsx',
                sheet_name=sheet_name,
                save_dir=save_dirs[i],
                target_url=target_urls[i])

    print('*************** Program Finished *****************')
