from pydantic import BaseModel
from .profile import PreferenceProfile
from typing import Optional


class ElectionState(BaseModel):
    """
    curr_round (an Int): current round number
    elected (a list of Candidate): candidates who pass a certain threshold to win an election
    eliminated (a list of Candidate): candidates who were eliminated (lost in the election)
    remaining (a list of Candidate): candidates who are still in the running
    rankings (a list of a set of Candidate): ranking of candidates with sets representing ties
    profile (a PreferenceProfile): a list of ballot types
    (schedule preferences) and their frequency of times
    winners_votes (a Dict of candidates and list of their ballots):
    each winner's list of ballots that elected them
    previous: an instance of Outcome representing the previous round
    """

    curr_round: int
    elected: list[str] = []
    eliminated: list[str] = []
    remaining: list[str] = []
    profile: PreferenceProfile
    winner_votes: Optional[dict] = None
    previous: Optional["ElectionState"] = None

    class Config:
        allow_mutation = False

    def get_all_winners(self) -> list[str]:
        """returns all winners from all rounds so far in order of first elected to last elected"""
        if self.previous:
            return self.previous.get_all_winners() + self.elected
        else:
            return self.elected

    def get_all_eliminated(self) -> list[str]:
        """returns all winners from all rounds so
        far in order of last eliminated to first eliminated
        """
        elim = self.eliminated.copy()
        elim.reverse()
        if self.previous:
            elim += self.previous.get_all_eliminated()
        return elim

    def get_rankings(self) -> list[str]:
        """returns all candidates in order of their ranking at the end of the current round"""

        return self.get_all_winners() + self.remaining + self.get_all_eliminated()

    def get_round_outcome(self, roundNum: int) -> dict:
        # {'elected':list[str], 'eliminated':list[str]}
        """returns a dictionary with elected and eliminated candidates"""
        if self.curr_round == roundNum:
            return {"elected": self.elected, "eliminated": self.eliminated}
        elif self.previous:
            return self.previous.get_round_outcome(roundNum)
        else:
            raise ValueError("Round number out of range")

    def changed_rankings(self) -> dict:
        """returns dict of (key) string candidates who changed
        ranking from previous round and (value) a tuple of (prevRank, newRank)
        """

        if not self.previous:
            raise ValueError("This is the first round, cannot compare previous ranking")

        prev_ranking: dict = {
            cand: index for index, cand in enumerate(self.previous.get_rankings())
        }
        curr_ranking: dict = {
            cand: index for index, cand in enumerate(self.get_rankings())
        }
        if curr_ranking == prev_ranking:
            return {}

        changes = {}
        for candidate, index in curr_ranking.items():
            if prev_ranking[candidate] != index:
                changes[candidate] = (prev_ranking[candidate], index)
        return changes

    ###############################################################################################

    # def add_winners_and_losers(self, winners: set[str], losers: set[str]) -> "Outcome":
    #   # example method, feel free to delete if not useful
    #  if not winners.issubset(self.remaining) or not losers.issubset(self.remaining):
    #     missing = (winners.difference(set(self.remaining)) |
    # (losersdifference(set(self.remaining)))
    #     raise ValueError(f"Cannot promote winners, {missing} not in remaining")
    # return Outcome(
    #     remaining=set(self.remaining).difference(winners | losers),
    #     elected=list(set(self.elected) | winners)
    #     eliminated=list(set(self.eliminated) | losers)
    # )

    #   def difference_remaining_candidates(
    #       self, prevOutcome1: "Outcome", prevOutcome2: "Outcome"
    #   ) -> float:
    #       """returns the fractional difference in number of
    #       remaining candidates; assumes ballots don't change by round
    #       """
    #       if (not prevOutcome1.get_profile()) or (not prevOutcome2.get_profile()):
    #           raise ValueError("Profile missing")
    # check if from same contest
    #        elif set(prevOutcome1.get_profile().ballots) != set(
    #            prevOutcome2.get_profile().ballots
    #        ):
    #            raise ValueError("Cannot compare outcomes from different elections")
    #
    #        remaining_diff = len(
    #            (set(prevOutcome1.remaining)).difference(prevOutcome2.remaining)
    #        )
    #        allcandidates = len(prevOutcome1.get_profile().get_candidates())
    #        return remaining_diff / allcandidates
