from daily_job_user import DailyJobUser
from join_raffle_user import JoinRaffleUser
from login_user import LoginUser


class User(DailyJobUser, JoinRaffleUser, LoginUser):
    pass

