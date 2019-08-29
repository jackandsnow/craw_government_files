import os

from lxml import etree

from common.tools import get_html_text, get_total_page_num, download_file, write_word_file, write_excel_file


class CrawShenZhenReport:

    def get_info_urls_of_reports(self, url):
        """
        根据url获取所有年份报告的url
        :param url: target url
        :return: page_urls list
        """
        html_text = get_html_text(url)
        html = etree.HTML(html_text)
        urls = html.xpath('//*[@id="top_bg"]/div/div[4]/div[7]/ul/li/a/@href')
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
            .replace('<', '(').replace('>', ')').replace('"', '-')  # 这里title都是相同的
        title = bytes.decode(base_infos[-3]).split('-')[0] + title  # 2019政府工作报告
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
        info_urls = self.get_info_urls_of_reports(target_url)   # 政府工作报告
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
    report = CrawShenZhenReport()

    # 政府工作报告
    save_dirs = [
        'data/政府工作报告'
    ]
    target_urls = [
        'http://www.sz.gov.cn/cn/xxgk/zfxxgj/gzbg/gwyzf'
    ]

    for i in range(0, len(target_urls)):
        if os.path.exists(save_dirs[i]) is False:
            os.mkdir(save_dirs[i])
        sheet_name = save_dirs[i].split('data/')[-1].replace('/', '_')
        report.run(excel_name='data/深圳市.xlsx',
                sheet_name=sheet_name,
                save_dir=save_dirs[i],
                target_url=target_urls[i])

    print('*************** Program Finished *****************')
