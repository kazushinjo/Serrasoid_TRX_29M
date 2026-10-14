"""ネットごとの線幅（mm）"""
HEAVY = {'+13V8', 'PA_D', 'T1_P', 'LPF_IN', 'LPF2', 'LPF3', 'TX_OUT', 'ANT', 'DRV_D', 'DCDC_IN'}
POWER = {'+8V', 'TX8V', 'RX8V', '+5V', '+5VT', '+5VA', '+3V3S', '+3V3X', 'XIAO_5V', 'RLY_C', 'AF_OUT', 'SPK'}
RF = {'PA_IN', 'PA_G', 'PA_SW', 'DRV_IN', 'DRV_G', 'DRV_SW', 'Q_BUF_C', 'Q_BUF_B', 'TXBPF_IN', 'TXBPF_OUT', 'TB1', 'TB2',
      'X32B', 'TXDRV', 'RX_ANT', 'RB1', 'RB2', 'GND'}
def width_of(n):
    n = n.lstrip('/')
    if n in HEAVY: return 1.2
    if n in POWER: return 0.6
    if n in RF: return 0.5
    return 0.3
