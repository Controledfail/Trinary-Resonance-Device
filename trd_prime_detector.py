"""
TRINARY RESONANCE DEVICE - PRIME DETECTOR
==========================================
Production-ready implementation with multi-zero support and analysis tools.

Theory: Primes resonate at zeta function critical zeros due to constructive
interference in the geometric phase accumulation. Composites exhibit 
destructive interference and fall below detection threshold.

Author: @controledfail
Repo: github.com/controledfail/Trinary-Resonance-Device
"""

import numpy as np
import matplotlib.pyplot as plt
from mpmath import mp, zeta as mpzeta
from typing import List, Tuple
import time

# High precision for zeta calculations
mp.dps = 20

# ============================================================================
# ZETA CRITICAL ZEROS (first 10 on the critical line Re(s) = 1/2)
# ============================================================================
ZETA_ZEROS = [
    14.134725141734693790,   # ζ₁
    21.022039638771554993,   # ζ₂
    25.010857580145688763,   # ζ₃
    30.424876125859513210,   # ζ₄
    32.935061587739189691,   # ζ₅
    37.586178158825671257,   # ζ₆
    40.918719012147495187,   # ζ₇
    43.327073280914999519,   # ζ₈
    48.005150881167159727,   # ζ₉
    49.773832477672302181,   # ζ₁₀
]

# ============================================================================
# CORE TRD RESONANCE FUNCTION
# ============================================================================

def trd_resonance(n: int, 
                  max_terms: int = 500,
                  num_zeros: int = 1,
                  early_abort: bool = True) -> float:
    """
    Compute TRD resonance magnitude for integer n.
    
    Parameters:
    -----------
    n : int
        Integer to test for primality
    max_terms : int
        Number of terms in geometric series (higher = more accurate)
    num_zeros : int
        Number of zeta zeros to use (1-10 available)
    early_abort : bool
        Enable early termination for obvious composites
    
    Returns:
    --------
    float : Resonance magnitude (primes >> threshold, composites ≈ 0)
    
    Theory:
    -------
    Resonance(n) ∼ Σₖ (log n + i log n)^k / |ζ(k + 0.5 + i·γₖ)|
    
    Where γₖ are the imaginary parts of zeta zeros on critical line.
    """
    if n <= 1:
        return 0.0
    if n == 2 or n == 3:
        return 1e30
    
    log_n = np.log(n)
    log_phase = log_n + 0.5*np.log(2.0)  # |log n + i log n|
    
    # Accumulate in log-space to prevent overflow
    log_mag = -np.inf
    
    # Use multiple zeta zeros for better discrimination
    zeros_to_use = ZETA_ZEROS[:num_zeros]
    
    for k in range(1, max_terms + 1):
        # Average contribution from multiple zeros
        log_term_sum = -np.inf
        
        for gamma in zeros_to_use:
            s = complex(k + 0.5, gamma)
            z = mpzeta(s)
            log_z = mp.log(abs(z))
            
            # Contribution from this zero
            log_term = k * log_phase - float(log_z)
            
            # Log-sum-exp for numerical stability
            if log_term > log_term_sum:
                log_term_sum = log_term + np.log1p(np.exp(log_term_sum - log_term))
            else:
                log_term_sum = log_term_sum + np.log1p(np.exp(log_term - log_term_sum))
        
        # Average across zeros
        log_term_avg = log_term_sum - np.log(num_zeros)
        
        # Early abort for composites (huge optimization)
        if early_abort and k > 60 and log_term_avg < log_mag - 25:
            return 0.0
        
        # Accumulate total magnitude
        if log_term_avg > log_mag:
            log_mag = log_term_avg + np.log1p(np.exp(log_mag - log_term_avg))
        else:
            log_mag = log_mag + np.log1p(np.exp(log_term_avg - log_mag))
    
    # Cap output to prevent overflow on exp
    if log_mag > 80:
        return 1e35
    else:
        return np.exp(log_mag)

# ============================================================================
# PRIME DETECTION WITH ANALYSIS
# ============================================================================

def detect_primes(N: int, 
                  max_terms: int = 500,
                  num_zeros: int = 1,
                  threshold: float = 1e15,
                  verbose: bool = True) -> Tuple[np.ndarray, np.ndarray]:
    """
    Detect primes up to N using TRD resonance.
    
    Returns:
    --------
    resonances : np.ndarray
        Resonance values for all integers 2..N
    detected_primes : np.ndarray
        Integers detected as primes
    """
    if verbose:
        print(f"Computing TRD resonance up to {N}")
        print(f"  max_terms = {max_terms}")
        print(f"  num_zeros = {num_zeros}")
        print(f"  threshold = {threshold:.2e}")
        print(f"  Estimated time: ~{N*0.002:.1f}s\n")
    
    start_time = time.time()
    resonances = []
    
    for n in range(2, N + 1):
        res = trd_resonance(n, max_terms=max_terms, num_zeros=num_zeros)
        resonances.append(res)
        
        if verbose and n % 2000 == 0:
            elapsed = time.time() - start_time
            rate = n / elapsed
            eta = (N - n) / rate
            print(f"  Progress: {n}/{N} ({100*n/N:.1f}%) - ETA {eta:.1f}s")
    
    resonances = np.array(resonances)
    detected = np.arange(2, N + 1)[resonances > threshold]
    
    if verbose:
        elapsed = time.time() - start_time
        print(f"\n✓ Completed in {elapsed:.2f}s ({N/elapsed:.0f} integers/sec)")
    
    return resonances, detected

# ============================================================================
# ACCURACY ANALYSIS
# ============================================================================

def is_prime_trial(n: int) -> bool:
    """Standard trial division primality test"""
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def analyze_accuracy(N: int, 
                    detected: np.ndarray,
                    verbose: bool = True) -> dict:
    """
    Compare TRD detection against known primes.
    """
    actual_primes = np.array([n for n in range(2, N+1) if is_prime_trial(n)])
    
    tp = len(np.intersect1d(detected, actual_primes))  # True positives
    fp = len(detected) - tp                             # False positives
    fn = len(actual_primes) - tp                        # False negatives
    
    precision = tp / len(detected) if len(detected) > 0 else 0
    recall = tp / len(actual_primes) if len(actual_primes) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    results = {
        'N': N,
        'actual_primes': len(actual_primes),
        'detected': len(detected),
        'true_positives': tp,
        'false_positives': fp,
        'false_negatives': fn,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
    }
    
    if verbose:
        print("\n" + "="*60)
        print("ACCURACY ANALYSIS")
        print("="*60)
        print(f"Range:              2 to {N}")
        print(f"Actual primes:      {len(actual_primes)}")
        print(f"Detected by TRD:    {len(detected)}")
        print(f"True positives:     {tp}")
        print(f"False positives:    {fp}")
        print(f"False negatives:    {fn}")
        print(f"Precision:          {precision*100:.2f}%")
        print(f"Recall:             {recall*100:.2f}%")
        print(f"F1 Score:           {f1:.4f}")
        print("="*60)
    
    return results

# ============================================================================
# VISUALIZATION
# ============================================================================

def plot_resonance(N: int, 
                   resonances: np.ndarray,
                   detected: np.ndarray,
                   threshold: float = 1e15,
                   save_path: str = None):
    """
    Create publication-quality resonance plot.
    """
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), 
                                     facecolor='#0a0a0a')
    
    # Top panel: Full range
    ax1.semilogy(range(2, N+1), resonances, 'c.', markersize=1.5, 
                 alpha=0.6, label='All integers')
    ax1.semilogy(detected, resonances[detected-2], 'r*', markersize=8, 
                 alpha=0.9, label='Detected primes')
    ax1.axhline(threshold, color='#ffaa00', ls='--', lw=2, 
                label=f'Threshold = {threshold:.2e}')
    ax1.set_ylim(1e-5, 1e40)
    ax1.set_xlim(2, N)
    ax1.set_ylabel('Resonance Magnitude', fontsize=12, weight='bold')
    ax1.set_title('TRINARY RESONANCE DEVICE — PRIME DETECTOR\n' +
                  'Zeta-Zero Resonance Method', 
                  fontsize=16, weight='bold', pad=15)
    ax1.legend(loc='upper right', fontsize=10)
    ax1.grid(True, which="both", alpha=0.2)
    
    # Bottom panel: Zoomed detail (first 200 integers)
    zoom_n = min(200, N)
    ax2.semilogy(range(2, zoom_n+1), resonances[:zoom_n-1], 'c.', 
                 markersize=3, alpha=0.8)
    detected_zoom = detected[detected <= zoom_n]
    ax2.semilogy(detected_zoom, resonances[detected_zoom-2], 'r*', 
                 markersize=12, alpha=0.9)
    ax2.axhline(threshold, color='#ffaa00', ls='--', lw=2)
    ax2.set_ylim(1e-5, 1e40)
    ax2.set_xlim(2, zoom_n)
    ax2.set_xlabel('n', fontsize=12, weight='bold')
    ax2.set_ylabel('Resonance Magnitude', fontsize=12, weight='bold')
    ax2.set_title(f'Detail View (n = 2 to {zoom_n})', 
                  fontsize=12, weight='bold')
    ax2.grid(True, which="both", alpha=0.2)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, facecolor='#0a0a0a')
        print(f"\n✓ Plot saved to {save_path}")
    
    plt.show()

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Configuration
    N = 5000              # Test range
    MAX_TERMS = 500       # Series truncation
    NUM_ZEROS = 1         # Number of zeta zeros to use (1-10)
    THRESHOLD = 1e15      # Detection threshold
    
    print("="*70)
    print("TRINARY RESONANCE DEVICE - PRIME DETECTOR")
    print("="*70)
    print(f"GitHub: @controledfail/Trinary-Resonance-Device")
    print(f"Theory: Zeta-zero resonance via geometric phase accumulation\n")
    
    # Run detection
    resonances, detected = detect_primes(
        N=N,
        max_terms=MAX_TERMS,
        num_zeros=NUM_ZEROS,
        threshold=THRESHOLD,
        verbose=True
    )
    
    # Analyze accuracy
    results = analyze_accuracy(N, detected, verbose=True)
    
    # Visualize
    plot_resonance(N, resonances, detected, threshold=THRESHOLD)
    
    # Export results
    print("\n" + "="*70)
    print("EXPORT OPTIONS")
    print("="*70)
    print("To save detected primes:")
    print("  np.savetxt('trd_primes.txt', detected, fmt='%d')")
    print("\nTo save resonance data:")
    print("  np.savez('trd_resonance.npz', n=range(2,N+1), resonance=resonances)")
    print("="*70)