from main import Plume_TestNet_Bot,logger
num=input('请输入创建钱包的数量:\n')
invited=input('请输入邀请码，只取后四位(PLUME-xxxx):\n')
assert num.isdigit(),'数量只能是整数'
assert int(num)>0,'数量只能是正数'
num=int(num)
bot=Plume_TestNet_Bot(invited=invited,show_point=False,init=False,wallet_path='./temp_wallets')
old_wallet=bot.get_wallets()
for i in range(num):
    bot.generate_and_save_wallet(f'temp_wallets/wallet_{len(bot.wallets)+i+1}.json')
bot.get_wallets()
for wallet in bot.wallets[len(old_wallet):len(bot.wallets)]:
    bot.login(wallet=wallet)
logger.success('刷邀请成功')

