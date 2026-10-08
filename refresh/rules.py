"""Immutable run identities. Historical recordings always use legacy rules."""
LEGACY='refresh24-v2'
ENHANCED='enhanced-connected-v1'
SUPPORTED=(LEGACY,ENHANCED)
def label(rules):return 'Original gameplay' if rules==LEGACY else 'Enhanced gameplay'
def for_theme(theme):return LEGACY if theme.style=='original' else ENHANCED
