import db

class User:

    def __init__(self, email, user_id, activity={}, votes={}, verified_email=False):

        self.email = email
        self.user_ID = user_ID
        self.activity = activity
        self.votes = votes
        self.verified_email = verified_email

class Opinion:

    def __init__(self, ID, text, activity, approved=None, scheduled=False, committee_jurisdiction=None):

        self.ID = ID
        self.text = text
        self.activity = activity
        self.approved = approved
        self.scheduled = scheduled
        self.committee_jurisdiction = committee_jurisdiction

    def count_votes(self):
        up_votes = 0
        down_votes = 0
        abstains = 0
        for user in db.user_cookies.values():
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
