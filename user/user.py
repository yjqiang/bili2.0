from user.daily_job_user import DailyJobUser
from user.join_raffle_user import JoinRaffleUser
from user.login_user import LoginUser


class User(DailyJobUser, JoinRaffleUser, LoginUser):
    pass

