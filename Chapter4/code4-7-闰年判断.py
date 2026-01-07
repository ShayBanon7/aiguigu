s = input('请输入年份：')


def method_name():
    year = int(s)
    if (not year % 4 and year % 100) or not year % 400:
        print('是闰年')
    else:
        print('不是闰年')


if s.isdigit():
    method_name()
else:
    print('请输入阿拉伯数字！')
    s = input('请输入年份：')
    if s.isdigit():
        method_name()
    else:
        print('尝试输入次数失败！')
