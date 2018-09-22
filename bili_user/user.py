from bili_user.daily_job_user import DailyJobUser
from bili_user.join_raffle_user import JoinRaffleUser
from bili_user.login_user import LoginUser


class User(DailyJobUser, JoinRaffleUser, LoginUser):
    pass

