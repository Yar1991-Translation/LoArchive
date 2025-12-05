"""
登录配置文件示例
请复制此文件为 login_info.py 并填入您的登录信息

Lofter 某次更新后需要登录才能访问大部分页面
请按以下步骤获取授权码：
1. 打开 Lofter 网页版并登录
2. 按 F12 打开开发者工具
3. 切换到 Application（应用）标签
4. 左侧选择 Cookies → https://www.lofter.com
5. 根据您的登录方式找到对应的值
"""

# 登录方式对应的 key
# - "LOFTER-PHONE-LOGIN-AUTH"  手机号登录
# - "Authorization"            Lofter ID 登录
# - "LOFTER_SESS"              QQ/微信/微博登录
# - "NTES_SESS"                邮箱登录
login_key = "LOFTER-PHONE-LOGIN-AUTH"

# 授权码（从浏览器 Cookies 中获取）
login_auth = "在这里填入您的授权码"



