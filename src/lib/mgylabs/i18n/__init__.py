from .extension import I18nExtension, NamespacedLocaleStr

__ = I18nExtension.contextual_gettext
_L = I18nExtension.gettext_lazy
_S = I18nExtension.contextual_namespaced_gettext

s_locale_str = NamespacedLocaleStr
# n_ = I18nExtension.contextual_ngettext
