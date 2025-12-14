import numpy as np


def simulate_hole_hardy(par_m, p, q, rng=None, max_shots=19):
    if rng is None:
        rng = np.random.default_rng()

    if p < 0 or q < 0 or p + q >= 1:
        raise ValueError("Need 0 <= p, 0 <= q, and p + q < 1")

    score = 0
    total_value = 0

    probs = np.array([p, q, 1 - p - q])
    values = np.array([2, 0, 1])

    while total_value < par_m:
        shot_type = rng.choice(3, p=probs)
        total_value += values[shot_type]
        score += 1

        if score > max_shots:
            raise RuntimeError("Exceeded max_shots. Check parameters.")

    return score


def simulate_many_holes(par_m, p, q, n_sim=100000, seed=None):
    rng = np.random.default_rng(seed)
    scores = []

    for _ in range(n_sim):
        s = simulate_hole_hardy(par_m, p, q, rng=rng)
        scores.append(s)

    scores = np.array(scores)
    unique, counts = np.unique(scores, return_counts=True)
    freqs = counts / counts.sum()
    return dict(zip(unique, freqs))


def hardy_distribution_markov(par_m, p, q, n_max=19):
    """
    Compute P(T_m = n) for n = 1, 2, ..., n_max
    using a finite Markov chain dynamic program.

    par_m : int
        Par of the hole (m).
    p : float
        Probability of a good shot (value 2).
    q : float
        Probability of a bad shot (value 0).
    n_max : int
        Maximum number of shots to compute. The true support is infinite,
        but tail probability past n_max is usually tiny if q is not too big.

    Returns
    -------
    scores : np.ndarray, shape (n_max,)
        Shot numbers 1, 2, ..., n_max.
    pmf : np.ndarray, shape (n_max,)
        Approximate Hardy distribution P(T_m = n) for each n.
        Sum of pmf will be <= 1 because of the truncated tail.
    """
    if p < 0 or q < 0 or p + q >= 1:
        raise ValueError("Need 0 <= p, 0 <= q, and p + q < 1")

    probs_good = p
    probs_bad = q
    probs_ord = 1 - p - q

    p_state = np.zeros(par_m, dtype=float)
    p_state[0] = 1.0

    pmf = np.zeros(n_max, dtype=float)

    for shot in range(1, n_max + 1):
        p_state_next = np.zeros_like(p_state)

        for s in range(par_m):
            prob_here = p_state[s]
            if prob_here == 0:
                continue

            new_val = s + 2
            if new_val >= par_m:
                pmf[shot - 1] += prob_here * probs_good
            else:
                p_state_next[new_val] += prob_here * probs_good

            new_val = s + 1
            if new_val >= par_m:
                pmf[shot - 1] += prob_here * probs_ord
            else:
                p_state_next[new_val] += prob_here * probs_ord

            p_state_next[s] += prob_here * probs_bad

        p_state = p_state_next

    scores = np.arange(1, n_max + 1)
    return scores, pmf

def hardy_finish_pmf_ij(par_m, i, j, p, q, n_max=20):
    """
    Markov chain first passage distribution to an absorbing state j
    for a hole with par = par_m.

    States:
      transient: 0, 1, ..., par_m - 1
      absorbing ordinary:   par_m
      absorbing exceptional: par_m + 1

    Each shot:
      good      with prob p       and value +2
      ordinary  with prob 1-p-q   and value +1
      bad       with prob q       and value +0

    If from a transient state s we get new_val = s + increment:
      if new_val >= par_m + 1   -> absorbing exceptional (par_m + 1)
      elif new_val == par_m     -> absorbing ordinary (par_m)
      else                      -> transient state new_val

    Parameters
    ----------
    par_m : int
        Par of the hole (3, 4, 5, ...).
    i : int
        Starting state (0 to par_m + 1).
    j : int
        Target absorbing state. Must be par_m (ordinary) or par_m + 1 (exceptional).
    p : float
        Probability of a good shot (value +2).
    q : float
        Probability of a bad shot (value +0).
        Ordinary shot has probability 1 - p - q (value +1).
    n_max : int
        Maximum number of additional shots to consider.

    Returns
    -------
    n_array : np.ndarray
        Shot counts n = 0, 1, ..., n_max.
    pmf : np.ndarray
        P(N = n) where N is the number of shots needed
        to first reach absorbing state j, starting from i.
        If you hit the other absorbing state first, that
        probability mass is dropped (does not count as success).
    """
    # basic checks
    if p < 0 or q < 0 or p + q >= 1:
        raise ValueError("Need 0 <= p, 0 <= q, and p + q < 1")
    if par_m < 1:
        raise ValueError("par_m must be at least 1")
    if not (0 <= i <= par_m + 1):
        raise ValueError(f"i must be between 0 and {par_m + 1}")
    if j not in (par_m, par_m + 1):
        raise ValueError(f"j must be par_m ({par_m}) or par_m + 1 ({par_m + 1})")

    p_good = p
    p_bad = q
    p_ord = 1 - p - q

    n_array = np.arange(0, n_max + 1)
    pmf = np.zeros_like(n_array, dtype=float)

    ordinary_abs = par_m
    exceptional_abs = par_m + 1
    other_abs = ordinary_abs if j == exceptional_abs else exceptional_abs

    # n = 0 case
    if i == j:
        pmf[0] = 1.0
        return n_array, pmf

    if i == other_abs:
        # Already in the competing absorbing state, never reach j
        return n_array, pmf

    # We only track transient states in p_state: indices 0..par_m-1
    p_state = np.zeros(par_m, dtype=float)
    if 0 <= i <= par_m - 1:
        p_state[i] = 1.0
    else:
        # i is an absorbing state but not j or other_abs (should not happen)
        return n_array, pmf

    for shot in range(1, n_max + 1):
        p_next = np.zeros_like(p_state)

        for s in range(par_m):  # transient states
            prob_here = p_state[s]
            if prob_here == 0.0:
                continue

            # Good shot: +2
            new_val = s + 2
            if new_val >= exceptional_abs:
                # goes to exceptional_abs
                if j == exceptional_abs:
                    pmf[shot] += prob_here * p_good
                # else hit other absorbing, ignore
            elif new_val == ordinary_abs:
                # goes to ordinary_abs
                if j == ordinary_abs:
                    pmf[shot] += prob_here * p_good
                # else ignore
            else:
                # still transient
                p_next[new_val] += prob_here * p_good

            # Ordinary shot: +1
            new_val = s + 1
            if new_val >= exceptional_abs:
                if j == exceptional_abs:
                    pmf[shot] += prob_here * p_ord
            elif new_val == ordinary_abs:
                if j == ordinary_abs:
                    pmf[shot] += prob_here * p_ord
            else:
                p_next[new_val] += prob_here * p_ord

            # Bad shot: +0
            # always stays transient
            p_next[s] += prob_here * p_bad

        p_state = p_next

    return n_array, pmf
