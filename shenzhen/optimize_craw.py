import os

import multiprocessing
from multiprocessing import Pool
from lxml import etree

from common.tools import get_html_text, download_file, write_word_file


def get_previous_bulletin_urls(url):
    """
    获取往期公报的 url
    :param url: target url
    :return: option_urls list, option_titles list
    """
    html_text = get_html_text(url)
    html = etree.HTML(html_text)
    links = html.xpath('//select[@name="select3"]/option/@value')
    option_titles = html.xpath('//select[@name="select3"]/option//text()')[1:]
    option_urls = [url]
    for l in range(1, len(links)):
        if option_titles[l].split('年')[0] == '2019':
            option_urls.append(url.split('2019')[0] + '2019/' + links[l].split('./')[-1])
        else:
            option_urls.append(url.split('2019')[0] + links[l].split('./')[-1])
    # print(option_urls)
    return option_urls, option_titles


def get_info_urls_of_bulletin(url):
    """
    爬取政府公报网页上的链接
    :param url: target url
    :return: info_urls list
    """
    page_content = get_html_text(url)
    html = etree.HTML(page_content)
    script_str = html.xpath('//div[@class="zx_zwgb_left"]//script/text()')[0]
    # print(script_str)
    links = script_str.split('opath.push("./')[1:]
    urls = list(map(lambda s: url + s.split('")')[0], links))
    return urls


def get_notification_infos(previous_title, url):
    """
    在通知文件页面爬取通知的内容
    :param previous_title: 往年期数
    :param url: info url
    :return: base_infos， content, attachments
    """
    page_content = get_html_text(url)
    if not page_content:
        return [], '', []
    html = etree.HTML(page_content)
    # ['期数', '索引号', '省份', '城市', '文件类型', '文号', '发布机构', '发布日期', '标题', '主题词']
    index = html.xpath('//div[@class="xx_con"]/p[1]/text()')
    aspect = html.xpath('//div[@class="xx_con"]/p[2]/text()')
    announced_by = html.xpath('//div[@class="xx_con"]/p[3]/text()')
    announced_date = html.xpath('//div[@class="xx_con"]/p[4]/text()')
    title = html.xpath('//div[@class="xx_con"]/p[5]/text()')
    document_num = html.xpath('//div[@class="xx_con"]/p[6]/text()')
    key_word = html.xpath('//div[@class="xx_con"]/p[7]/text()')
    base_infos = [[previous_title], index, ['广东省'], ['深圳市'], aspect, document_num, announced_by, announced_date,
                  title, key_word]
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
    print('Get Content from ******************', url)
    return base_infos, contents, attachments


def write_notification_to_docx(save_dir, base_infos, contents, attachments):
    """
    保存通知的详细信息到word文件
    :param save_dir: 保存的路径
    :param base_infos: 通知的基本信息（'索引号', '省份', '城市', '文件类型', '文号', '发布机构', '发布日期', '标题', '主题词'）
    :param contents: 通知内容
    :param attachments: 附件信息
    :return: None
    """
    aspect = bytes.decode(base_infos[-6]) if base_infos[-6] != ' ' else '其他'
    aspect_dir = save_dir + '/' + aspect
    if os.path.exists(aspect_dir) is False:
        os.mkdir(aspect_dir)
    title = bytes.decode(base_infos[-2]).replace('/', '-').replace(' ', '') \
        .replace('<', '(').replace('>', ')').replace('"', '-')
    # 下载附件
    if len(attachments) > 0:
        # 有附件则要新建目录
        aspect_dir = aspect_dir + '/' + title
        os.mkdir(aspect_dir)
        for attachment in attachments:
            suffix = attachment[1].split('.')[-1]
            attach_name = attachment[0] + '.' + suffix if suffix not in attachment[0] else attachment[0]
            # 不下载mp4视频
            if suffix != 'mp4':
                download_file(file_url=attachment[1], filename=aspect_dir + '/' + attach_name)
    # 处理文件名过长
    filename = aspect_dir + '/' + title + '.docx'
    filename = aspect_dir + '/...' + title[-50:] + '.docx' if len(filename) > 180 else filename
    # 写入word文档
    write_word_file(filename=filename,
                    title=title, data_list=[contents])


def craw_job(target_url, target_title, save_dir):
    """
    设置爬虫任务
    :param target_url: url
    :param target_title: title
    :param save_dir: save directory
    :return: None
    """
    info_urls = get_info_urls_of_bulletin(target_url)  # 政府公报
    for info_url in info_urls:
        if '' != info_url:
            # print('Get Information From ', info_url)
            base_infos, contents, attachments = get_notification_infos(target_title, info_url)
            # 剔除掉没有爬到内容的通知
            if contents.strip() != '':
                write_notification_to_docx(save_dir, base_infos, contents, attachments)


if __name__ == '__main__':
    """
    This file is optimized for 'craw_shenzhen_gov_bulletin.py'.
    This file mainly implements crawling data with multi processes, which can improve the efficiency of crawling. 
    """
    MAX_CPU_NUM = multiprocessing.cpu_count()
    pool = Pool(MAX_CPU_NUM - 2)
    # 政府公报
    save_dirs = [
        'bulletin'
    ]
    target_urls = [
        'http://www.sz.gov.cn/zfgb/2019/gb1099_181240/'
    ]

    for i in range(0, len(target_urls)):
        if os.path.exists(save_dirs[i]) is False:
            os.mkdir(save_dirs[i])
        previous_urls, previous_titles = get_previous_bulletin_urls(target_urls[i])
        for p in range(len(previous_urls)):
            # 创建往期目录
            previous_dir = save_dirs[i] + '/' + previous_titles[p]
            if os.path.exists(previous_dir) is False:
                os.mkdir(previous_dir)
            # 爬取往期通知
            pool.apply_async(craw_job, args=(previous_urls[p], previous_titles[p], previous_dir,))

    pool.close()  # 关闭进程池，不再接受任务提交
    pool.join()  # 等待所有任务完成
