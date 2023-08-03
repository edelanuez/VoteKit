from .profile import PreferenceProfile
from .ballot import Ballot
from .election_state import ElectionState
from typing import Callable
import random
from fractions import Fraction
from copy import deepcopy
from collections import namedtuple


class STV:
    """
    Class for single-winner IRV and multi-winner STV elections
    """

    def __init__(self, profile: PreferenceProfile, transfer: Callable, seats: int):
        """
        profile (PreferenceProfile): initial perference profile
        transfer (function): vote transfer method such as fractional transfer
        seats (int): number of winners/size of committee
        """
        self.__profile = profile
        self.transfer = transfer
        self.seats = seats
        self.election_state = ElectionState(
            curr_round=0,
            elected=[],
            eliminated=[],
            remaining=[
                cand
                for cand, votes in compute_votes(
                    profile.get_candidates(), profile.get_ballots()
                )
            ],
            profile=profile,
        )
        self.threshold = self.get_threshold()

    # can cache since it will not change throughout rounds
    def get_threshold(self) -> int:
        """
        Droop quota
        Droop quota
        """
        return int(self.election_state.profile.num_ballots() / (self.seats + 1) + 1)

    def next_round(self) -> bool:
        """
        Determines if the number of seats has been met to call election
        """
        return len(self.election_state.get_all_winners()) != self.seats

    def run_step(self) -> ElectionState:
        """
        Simulates one round an STV election
        """
        ##TODO:must change the way we pass winner_votes
        remaining: list[str] = self.election_state.remaining
        ballots: list[Ballot] = self.election_state.profile.get_ballots()
        fp_votes = compute_votes(remaining, ballots)  ##fp means first place
        elected = []
        eliminated = []

        # if number of remaining candidates equals number of remaining seats,
        # everyone is elected
        if len(remaining) == self.seats - len(self.election_state.get_all_winners()):
            elected = [cand for cand, votes in fp_votes]
            remaining = []
            ballots = []
            # TODO: sort remaining candidates by vote share

        # elect all candidates who crossed threshold
        elif fp_votes[0].votes >= self.threshold:
            for candidate, votes in fp_votes:
                if votes >= self.threshold:
                    elected.append(candidate)
                    remaining.remove(candidate)
                    ballots = self.transfer(
                        candidate,
                        ballots,
                        {cand: votes for cand, votes in fp_votes},
                        self.threshold,
                    )
        # since no one has crossed threshold, eliminate one of the people
        # with least first place votes
        elif self.next_round():
            lp_votes = min([votes for cand, votes in fp_votes])
            lp_candidates = [
                candidate for candidate, votes in fp_votes if votes == lp_votes
            ]
            # is this how to break ties, can be different based on locality
            lp_cand = random.choice(lp_candidates)
            eliminated.append(lp_cand)
            ballots = remove_cand(lp_cand, ballots)
            remaining.remove(lp_cand)

        self.election_state = ElectionState(
            curr_round=self.election_state.curr_round + 1,
            elected=elected,
            eliminated=eliminated,
            remaining=remaining,
            profile=PreferenceProfile(ballots=ballots),
            previous=self.election_state,
        )
        return self.election_state

    def run_election(self) -> ElectionState:
        """
        Runs complete STV election
        """
        if not self.next_round():
            raise ValueError(
                f"Length of elected set equal to number of seats ({self.seats})"
            )

        while self.next_round():
            self.run_step()

        return self.election_state

    def get_init_profile(self):
        "returns the initial profile of the election"
        return self.__profile


## Election Helper Functions
CandidateVotes = namedtuple("CandidateVotes", ["cand", "votes"])


def compute_votes(candidates: list, ballots: list[Ballot]) -> list[CandidateVotes]:
    """
    Computes first place votes for all candidates in a preference profile
    """
    votes = {}
    for candidate in candidates:
        weight = Fraction(0)
        for ballot in ballots:
            if ballot.ranking and ballot.ranking[0] == {candidate}:
                weight += ballot.weight
        votes[candidate] = weight

    ordered = [
        CandidateVotes(cand=key, votes=value)
        for key, value in sorted(votes.items(), key=lambda x: x[1], reverse=True)
    ]

    return ordered


def fractional_transfer(
    winner: str, ballots: list[Ballot], votes: dict, threshold: int
) -> list[Ballot]:
    """
    Calculates fractional transfer from winner, then removes winner
    from the list of ballots
    """
    transfer_value = (votes[winner] - threshold) / votes[winner]

    for ballot in ballots:
        if ballot.ranking and ballot.ranking[0] == {winner}:
            ballot.weight = ballot.weight * transfer_value

    return remove_cand(winner, ballots)


def remove_cand(removed_cand: str, ballots: list[Ballot]) -> list[Ballot]:
    """
    Removes candidate from ranking of the ballots
    """
    update = deepcopy(ballots)

    for n, ballot in enumerate(update):
        new_ranking = [
            candidate for candidate in ballot.ranking if candidate != {removed_cand}
        ]
        update[n].ranking = new_ranking

    return update
