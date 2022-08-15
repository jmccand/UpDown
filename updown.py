import db
import datetime

class User:

    def __init__(self, email, user_ID, activity={}, votes={}, verified_result=False, obselete=False):

        self.email = email
        self.user_ID = user_ID
        self.activity = activity
        self.votes = votes
        self.verified_result = verified_result
        self.obselete = obselete

class Opinion:

    def __init__(self, ID, text, activity, approved=None, scheduled=False, reserved_for=None, bill='', resolved=False):

        self.ID = ID
        self.text = text
        self.activity = activity
        self.approved = approved
        self.scheduled = scheduled
        self.reserved_for = reserved_for
        self.bill = bill
        self.resolved = resolved

    def count_votes(self):
        up_votes = 0
        down_votes = 0
        abstains = 0
        for user in db.user_ids.values():
            if user.verified_email and str(self.ID) in user.votes:
                    this_vote = user.votes[str(self.ID)][-1][0]
                    #print(f'{user.email} has voted {this_vote}')
                    if this_vote == 'up':
                        up_votes += 1
                    elif this_vote == 'down':
                        down_votes += 1
                    elif this_vote == 'abstain':
                        abstains += 1
                    else:
                        raise ValueError(f'Found a vote other than up, down, or abstain: {this_vote}')
        return up_votes, down_votes, abstains

    def care_agree_percent(self):
        up, down, abstain = self.count_votes()
        care = 0
        agree = 0
        if up + down + abstain > 0:
            care = (up + down) / (up + down + abstain) * 100
            if up + down > 0:
                agree = up / (up + down) * 100
        return care, agree

    def is_after_voting(self):
        see_day = None
        today_date = datetime.date.today()
        if (today_date.weekday() + 1) % 7 < 3:
            see_day = today_date - datetime.timedelta((today_date.weekday() + 1) % 7)
        elif (today_date.weekday() + 1) % 7 > 3:
            see_day = today_date - datetime.timedelta((today_date.weekday() + 1) % 7 - 4)
        else:
            see_day = today_date

        return self.scheduled and self.activity[2][0][0] < today_date and str(self.ID) not in db.opinions_calendar.get(str(see_day), set())

    def rankings(self):
        my_care, my_agree = self.care_agree_percent()
        my_overall = my_care * my_agree
        care_rank = 1
        agree_rank = 1
        overall_rank = 1
        for opinion in db.opinions_database.values():
            this_care, this_agree = opinion.care_agree_percent()
            this_overall = this_care * this_agree
            if this_care > my_care:
                care_rank += 1
            if this_agree > my_agree:
                agree_rank += 1
            if this_overall > my_overall:
                overall_rank += 1
        return care_rank, agree_rank, overall_rank
 
