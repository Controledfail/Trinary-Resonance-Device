import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from sympy import primerange

# ============================================================================
# CORE UTILITIES
# ============================================================================

def scramble_phases(zeros):
    """
    Destroys relative phase order while preserving density and endpoints.
    Uses diff-shuffle-cumsum to maintain spectral character.
    """
    z = zeros.copy()
    diffs = np.diff(z)
    np.random.shuffle(diffs)
    scrambled = np.cumsum(np.insert(diffs, 0, z[0]))
    return scrambled

def compute_S(zeros, t_grid, normalize=True):
    """
    Compute zero-phase interference proxy for S(t).
    
    S(t) ~ Σ sin(γ_k log(t) / 2π) / √γ_k
    """
    S = np.zeros_like(t_grid)
    for gamma in zeros:
        phase = gamma * np.log(t_grid) / (2 * np.pi)
        S += np.sin(phase) / np.sqrt(gamma)
    
    if normalize:
        S = S / np.std(S)
    
    return S

def detect_minima(S, t_grid, min_distance=1.0):
    """
    Blind local minima detection.
    Returns detected positions in t-space (log-space).
    """
    dt = t_grid[1] - t_grid[0]
    distance_samples = int(min_distance / dt)
    
    minima_idx = find_peaks(-S, distance=distance_samples)[0]
    return t_grid[minima_idx]

def match_bijective(detected, primes, tolerance=0.5):
    """
    Greedy monotone bijection in log space.
    Each detection matched to at most one prime, and vice versa.
    
    Returns: list of (detected_log, prime_log, error) tuples
    """
    detected = np.sort(detected)
    log_primes = np.log(primes)
    
    matches = []
    used_primes = set()
    
    for m in detected:
        # Find nearest unused prime
        available = [i for i in range(len(log_primes)) if i not in used_primes]
        if not available:
            break
            
        errors = [abs(log_primes[i] - m) for i in available]
        best_idx = available[np.argmin(errors)]
        error = abs(log_primes[best_idx] - m)
        
        if error < tolerance:
            matches.append((m, log_primes[best_idx], error))
            used_primes.add(best_idx)
    
    return matches

def compute_match_quality(zeros, t_grid, primes, tolerance=0.5):
    """
    Compute match quality Q = (# correct matches) / (# detections)
    """
    S = compute_S(zeros, t_grid)
    detected = detect_minima(S, t_grid)
    matches = match_bijective(detected, primes, tolerance)
    
    if len(detected) == 0:
        return 0.0
    
    return len(matches) / len(detected)

# ============================================================================
# Q1: PHASE-ORDER NULL TEST
# ============================================================================

def test_Q1_phase_scrambling(zeros, t_grid, primes, n_trials=1000, tolerance=0.5):
    """
    H0: Any set of phases with same density produces comparable alignment.
    H1: Only ordered Riemann zeros produce alignment.
    """
    print("\n" + "="*70)
    print("Q1: PHASE-ORDER NULL TEST")
    print("="*70)
    print("Testing whether specific zero ordering matters...")
    print(f"Running {n_trials} scrambled trials...")
    
    # Compute real quality
    Q_real = compute_match_quality(zeros, t_grid, primes, tolerance)
    
    # Compute null distribution
    Q_null = []
    for i in range(n_trials):
        if (i+1) % 100 == 0:
            print(f"  Trial {i+1}/{n_trials}...")
        scrambled = scramble_phases(zeros)
        Q_null.append(compute_match_quality(scrambled, t_grid, primes, tolerance))
    
    Q_null = np.array(Q_null)
    
    # Statistical analysis
    p_value = np.mean(Q_null >= Q_real)
    z_score = (Q_real - Q_null.mean()) / Q_null.std() if Q_null.std() > 0 else np.inf
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.hist(Q_null, bins=50, alpha=0.7, label='Phase-scrambled', color='gray', edgecolor='black')
    plt.axvline(Q_real, color='red', linewidth=3, label=f'Ordered zeros (Q={Q_real:.3f})')
    plt.axvline(Q_null.mean(), color='blue', linestyle='--', linewidth=2, 
                label=f'Null mean (Q={Q_null.mean():.3f})')
    plt.xlabel('Match Quality Q', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.title('Q1: Phase Order Null Test\n(Does zero ordering matter?)', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(alpha=0.3)
    
    # Add statistics box
    textstr = f'p-value: {p_value:.4f}\nz-score: {z_score:.2f}\nσ above mean: {z_score:.1f}'
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    plt.text(0.02, 0.98, textstr, transform=plt.gca().transAxes, fontsize=10,
             verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    plt.show()
    
    # Results
    results = {
        "Q_real": Q_real,
        "Q_null_mean": Q_null.mean(),
        "Q_null_std": Q_null.std(),
        "p_value": p_value,
        "z_score": z_score
    }
    
    print("\nRESULTS:")
    print(f"  Q_real = {Q_real:.4f}")
    print(f"  Q_null = {Q_null.mean():.4f} ± {Q_null.std():.4f}")
    print(f"  p-value = {p_value:.4f}")
    print(f"  z-score = {z_score:.2f}")
    
    if p_value < 0.01:
        print(f"\n✓ PASS: Phase ordering is significant (p < 0.01)")
    elif p_value < 0.05:
        print(f"\n⚠ MARGINAL: Phase ordering shows trend (p < 0.05)")
    else:
        print(f"\n✗ FAIL: Phase ordering not significant (p ≥ 0.05)")
    
    return results

# ============================================================================
# Q2: ERROR SCALING LAW TEST
# ============================================================================

def test_Q2_error_scaling(zeros, t_grid, primes, tolerance=0.5):
    """
    Test whether errors obey: |log(p̂) - log(p)| ≲ max(Δt/2, C/log p)
    """
    print("\n" + "="*70)
    print("Q2: ERROR SCALING LAW TEST")
    print("="*70)
    print("Testing whether errors are resolution-limited...")
    
    # Compute and detect
    S = compute_S(zeros, t_grid)
    detected = detect_minima(S, t_grid)
    
    # Bijective matching
    matches = match_bijective(detected, primes, tolerance)
    
    if len(matches) == 0:
        print("✗ FAIL: No matches found")
        return None
    
    # Extract matched pairs
    detected_log = np.array([m[0] for m in matches])
    true_log = np.array([m[1] for m in matches])
    errors = np.array([m[2] for m in matches])
    p_vals = np.exp(true_log)
    
    # Theoretical bound
    dt = t_grid[1] - t_grid[0]
    expected = np.maximum(dt/2, 1.0 / true_log)
    
    # Count violations
    violations = np.sum(errors > expected)
    violation_rate = violations / len(errors)
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.loglog(p_vals, errors, 'o', alpha=0.6, markersize=5, label='Observed errors')
    plt.loglog(p_vals, expected, 'r--', linewidth=2, label='Theoretical bound')
    plt.xlabel('Prime p', fontsize=12)
    plt.ylabel('|log(p̂) − log(p)|', fontsize=12)
    plt.title('Q2: Error Scaling vs Asymptotic Bound\n(Are errors resolution-limited?)', 
              fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(alpha=0.3, which='both')
    
    # Add statistics box
    textstr = f'Mean error: {errors.mean():.4f}\nMedian error: {np.median(errors):.4f}\nViolations: {violations}/{len(errors)} ({violation_rate*100:.1f}%)'
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    plt.text(0.02, 0.98, textstr, transform=plt.gca().transAxes, fontsize=10,
             verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    plt.show()
    
    # Results
    results = {
        "num_matches": len(matches),
        "mean_error": errors.mean(),
        "median_error": np.median(errors),
        "max_error": errors.max(),
        "violations": violations,
        "violation_rate": violation_rate
    }
    
    print("\nRESULTS:")
    print(f"  Matches: {len(matches)}")
    print(f"  Mean error: {errors.mean():.4f}")
    print(f"  Median error: {np.median(errors):.4f}")
    print(f"  Max error: {errors.max():.4f}")
    print(f"  Violations: {violations}/{len(errors)} ({violation_rate*100:.1f}%)")
    
    if violation_rate < 0.1:
        print(f"\n✓ PASS: Errors are resolution-limited (<10% violations)")
    elif violation_rate < 0.25:
        print(f"\n⚠ MARGINAL: Most errors within bound (<25% violations)")
    else:
        print(f"\n✗ FAIL: High violation rate (≥25%)")
    
    return results

# ============================================================================
# Q3: OUT-OF-SAMPLE PREDICTION TEST
# ============================================================================

def test_Q3_prediction(zeros, t_grid, primes, t_max, n_cutoffs=15):
    """
    Test whether low zeros encode high primes via extrapolation.
    """
    print("\n" + "="*70)
    print("Q3: OUT-OF-SAMPLE PREDICTION TEST")
    print("="*70)
    print("Testing predictive encoding beyond training range...")
    
    cutoffs = np.linspace(zeros[10], zeros[len(zeros)//2], n_cutoffs)
    recalls = []
    precisions = []
    
    for i, T_cut in enumerate(cutoffs):
        print(f"  Cutoff {i+1}/{n_cutoffs}: T={T_cut:.1f}...")
        
        # Train on zeros up to T_cut
        zeros_train = zeros[zeros <= T_cut]
        
        # Compute S and detect
        S = compute_S(zeros_train, t_grid)
        detected = detect_minima(S, t_grid)
        
        # Focus on extrapolation region [T_cut, t_max]
        detected_test = detected[(detected > T_cut) & (detected < t_max)]
        primes_test = primes[(np.log(primes) > T_cut) & (np.log(primes) < t_max)]
        
        if len(primes_test) == 0:
            recalls.append(np.nan)
            precisions.append(np.nan)
            continue
        
        # Match in test region
        matches = match_bijective(detected_test, primes_test, tolerance=0.5)
        
        recall = len(matches) / len(primes_test) if len(primes_test) > 0 else 0
        precision = len(matches) / len(detected_test) if len(detected_test) > 0 else 0
        
        recalls.append(recall)
        precisions.append(precision)
    
    recalls = np.array(recalls)
    precisions = np.array(precisions)
    
    # Plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Recall plot
    ax1.plot(cutoffs, recalls, 'o-', linewidth=2, markersize=8, color='blue')
    ax1.axhline(0.8, linestyle='--', color='orange', linewidth=2, label='Strong signal (0.8)')
    ax1.axhline(0.5, linestyle='--', color='gray', linewidth=2, label='Random baseline (0.5)')
    ax1.set_xlabel('Zero cutoff T_cut', fontsize=12)
    ax1.set_ylabel('Recall (extrapolation region)', fontsize=12)
    ax1.set_title('Recall: Fraction of primes detected', fontsize=12, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(alpha=0.3)
    
    # Precision plot
    ax2.plot(cutoffs, precisions, 'o-', linewidth=2, markersize=8, color='green')
    ax2.axhline(0.8, linestyle='--', color='orange', linewidth=2, label='Strong signal (0.8)')
    ax2.set_xlabel('Zero cutoff T_cut', fontsize=12)
    ax2.set_ylabel('Precision (extrapolation region)', fontsize=12)
    ax2.set_title('Precision: Fraction of detections that are primes', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(alpha=0.3)
    
    plt.suptitle('Q3: Out-of-Sample Prediction Test\n(Do low zeros encode high primes?)', 
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show()
    
    # Results
    mean_recall = np.nanmean(recalls)
    mean_precision = np.nanmean(precisions)
    
    results = {
        "cutoffs": cutoffs,
        "recalls": recalls,
        "precisions": precisions,
        "mean_recall": mean_recall,
        "mean_precision": mean_precision
    }
    
    print("\nRESULTS:")
    print(f"  Mean recall: {mean_recall:.3f}")
    print(f"  Mean precision: {mean_precision:.3f}")
    
    if mean_recall > 0.8 and mean_precision > 0.8:
        print(f"\n✓ PASS: Strong predictive encoding (R>0.8, P>0.8)")
    elif mean_recall > 0.6:
        print(f"\n⚠ MARGINAL: Moderate predictive signal (R>0.6)")
    else:
        print(f"\n✗ FAIL: Weak predictive encoding (R≤0.6)")
    
    return results

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # First 50 verified Riemann zeros
    ZEROS = np.array([
        14.134725, 21.022040, 25.010858, 30.424876, 32.935062,
        37.586178, 40.918719, 43.327073, 48.005151, 49.773832,
        52.970321, 56.446248, 59.347044, 60.831778, 65.112544,
        67.079811, 69.546402, 72.067158, 75.704691, 77.144840,
        79.337375, 82.910381, 84.735493, 87.425275, 88.809111,
        92.491899, 94.651344, 95.870634, 98.831194, 101.317851,
        103.725538, 105.446623, 107.168611, 111.029536, 111.874659,
        114.320220, 116.226680, 118.790782, 121.370125, 122.946829,
        124.256819, 127.516683, 129.578704, 131.087688, 133.497737,
        134.756509, 138.116042, 139.736209, 141.123707, 143.111846
    ])
    
    t_max = 150
    t_grid = np.linspace(10, t_max, 10000)
    
    prime_limit = int(np.exp(t_max))
    primes = np.array(list(primerange(2, min(prime_limit, 10**7))))
    
    print(f"\nRiemann Zero Prime Detection: Three Statistical Tests")
    print("="*70)
    print(f"\nInitialized with:")
    print(f"  {len(ZEROS)} Riemann zeros")
    print(f"  {len(primes)} primes up to {primes[-1]}")
    print(f"  t-grid: [{t_grid[0]:.1f}, {t_grid[-1]:.1f}] with {len(t_grid)} points")
    
    # Run all three tests
    results_Q1 = test_Q1_phase_scrambling(ZEROS, t_grid, primes, n_trials=500)
    results_Q2 = test_Q2_error_scaling(ZEROS, t_grid, primes)
    results_Q3 = test_Q3_prediction(ZEROS, t_grid, primes, t_max)
    
    print("\n" + "="*70)
    print("ALL TESTS COMPLETE")
    print("="*70)
    print("\nSUMMARY:")
    print(f"  Q1 (Phase Order): {'PASS' if results_Q1['p_value'] < 0.01 else 'FAIL'} (p={results_Q1['p_value']:.4f})")
    if results_Q2:
        print(f"  Q2 (Error Scaling): {'PASS' if results_Q2['violation_rate'] < 0.1 else 'FAIL'} ({results_Q2['violation_rate']*100:.1f}% violations)")
    print(f"  Q3 (Prediction): {'PASS' if results_Q3['mean_recall'] > 0.8 else 'FAIL'} (recall={results_Q3['mean_recall']:.3f})")
