/**
 * ProfileScreen.tsx — Arabic (RTL) profile screen for an Expo app.
 *
 * RTL notes:
 * - Layout is RTL whether or not the app called I18nManager.forceRTL(true):
 *   the root View sets `direction: 'rtl'`, so every `flexDirection: 'row'`
 *   starts on the right, and `start`/`end` (marginStart, paddingEnd, ...)
 *   resolve to the correct physical side. No `left`/`right` is used for layout.
 * - Recommended at app entry (requires a reload to take effect):
 *     I18nManager.allowRTL(true); I18nManager.forceRTL(true);
 *   or in app.json: { "expo": { "extra": { "supportsRTL": true, "forcesRTL": true } } }
 * - Directional icons (chevron, logout arrow) point toward the reading direction.
 * - The phone number is isolated as LTR so "+966" stays at its start.
 */
import React from 'react';
import {
  Alert,
  I18nManager,
  Image,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextStyle,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

type IoniconName = React.ComponentProps<typeof Ionicons>['name'];

type SettingsItem = {
  key: string;
  label: string;
  icon: IoniconName;
  onPress?: () => void;
};

type User = {
  name: string;
  phone: string; // E.164-ish, displayed LTR
  avatarUrl?: string;
};

type ProfileScreenProps = {
  user?: User;
  onLogout?: () => void;
  onNavigate?: (key: string) => void;
};

const DEFAULT_USER: User = {
  name: 'محمد عبدالله',
  phone: '+966 50 123 4567',
  avatarUrl: 'https://i.pravatar.cc/300?img=12',
};

const COLORS = {
  background: '#F4F5F7',
  surface: '#FFFFFF',
  text: '#1A1D23',
  textMuted: '#6B7280',
  separator: '#E5E7EB',
  primary: '#0E7C66',
  primarySoft: '#E6F4F0',
  danger: '#D92D20',
  dangerSoft: '#FDECEA',
  chevron: '#9CA3AF',
};

/**
 * React Native swaps textAlign 'left'/'right' when I18nManager.isRTL is true.
 * We want text aligned to the *start* of an RTL line (physical right) in both cases.
 */
const TEXT_START: TextStyle['textAlign'] = I18nManager.isRTL ? 'left' : 'right';

/** Unicode isolates keep LTR runs (phone numbers) intact inside RTL text. */
const LRI = '⁦';
const PDI = '⁩';

const ProfileScreen: React.FC<ProfileScreenProps> = ({
  user = DEFAULT_USER,
  onLogout,
  onNavigate,
}) => {
  const settings: SettingsItem[] = [
    { key: 'account', label: 'معلومات الحساب', icon: 'person-outline' },
    { key: 'notifications', label: 'الإشعارات', icon: 'notifications-outline' },
    { key: 'language', label: 'اللغة', icon: 'language-outline' },
    { key: 'privacy', label: 'الخصوصية والأمان', icon: 'shield-checkmark-outline' },
    { key: 'payment', label: 'طرق الدفع', icon: 'card-outline' },
    { key: 'help', label: 'المساعدة والدعم', icon: 'help-circle-outline' },
    { key: 'about', label: 'عن التطبيق', icon: 'information-circle-outline' },
  ];

  const handleLogout = () => {
    Alert.alert('تسجيل الخروج', 'هل أنت متأكد أنك تريد تسجيل الخروج؟', [
      { text: 'إلغاء', style: 'cancel' },
      { text: 'تسجيل الخروج', style: 'destructive', onPress: onLogout },
    ]);
  };

  const initials = user.name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join(' ');

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
      <StatusBar barStyle="dark-content" backgroundColor={COLORS.background} />
      <View style={styles.rtlRoot}>
        <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
          <Text style={styles.screenTitle} accessibilityRole="header">
            الملف الشخصي
          </Text>

          {/* Header: avatar, name, phone */}
          <View style={styles.header}>
            {user.avatarUrl ? (
              <Image
                source={{ uri: user.avatarUrl }}
                style={styles.avatar}
                accessibilityLabel={`صورة ${user.name}`}
              />
            ) : (
              <View style={[styles.avatar, styles.avatarFallback]}>
                <Text style={styles.avatarInitials}>{initials}</Text>
              </View>
            )}
            <Text style={styles.name} numberOfLines={1}>
              {user.name}
            </Text>
            <View style={styles.phoneRow}>
              <Ionicons name="call-outline" size={16} color={COLORS.textMuted} />
              <Text
                style={styles.phone}
                accessibilityLabel={`رقم الجوال ${user.phone}`}
              >
                {`${LRI}${user.phone}${PDI}`}
              </Text>
            </View>
          </View>

          {/* Settings list */}
          <Text style={styles.sectionTitle}>الإعدادات</Text>
          <View style={styles.card}>
            {settings.map((item, index) => (
              <Pressable
                key={item.key}
                onPress={() => (item.onPress ? item.onPress() : onNavigate?.(item.key))}
                accessibilityRole="button"
                accessibilityLabel={item.label}
                android_ripple={{ color: COLORS.separator }}
                style={({ pressed }) => [styles.row, pressed && styles.rowPressed]}
              >
                <View style={styles.iconWrap}>
                  <Ionicons name={item.icon} size={20} color={COLORS.primary} />
                </View>
                <View
                  style={[
                    styles.rowBody,
                    index < settings.length - 1 && styles.rowDivider,
                  ]}
                >
                  <Text style={styles.rowLabel} numberOfLines={1}>
                    {item.label}
                  </Text>
                  {/* "Forward" in RTL points left. */}
                  <Ionicons name="chevron-back" size={18} color={COLORS.chevron} />
                </View>
              </Pressable>
            ))}
          </View>

          {/* Logout */}
          <Pressable
            onPress={handleLogout}
            accessibilityRole="button"
            accessibilityLabel="تسجيل الخروج"
            style={({ pressed }) => [styles.logoutButton, pressed && styles.logoutPressed]}
          >
            <Ionicons
              name="log-out-outline"
              size={20}
              color={COLORS.danger}
              style={styles.flipForRtl}
            />
            <Text style={styles.logoutText}>تسجيل الخروج</Text>
          </Pressable>

          <Text style={styles.version}>{`الإصدار ${LRI}1.0.0${PDI}`}</Text>
        </ScrollView>
      </View>
    </SafeAreaView>
  );
};

const AVATAR_SIZE = 96;

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  rtlRoot: {
    flex: 1,
    direction: 'rtl',
  },
  content: {
    paddingHorizontal: 16,
    paddingBottom: 32,
  },
  screenTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.text,
    textAlign: TEXT_START,
    writingDirection: 'rtl',
    marginTop: 8,
    marginBottom: 16,
  },

  // Header
  header: {
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    paddingVertical: 24,
    paddingHorizontal: 16,
    marginBottom: 24,
  },
  avatar: {
    width: AVATAR_SIZE,
    height: AVATAR_SIZE,
    borderRadius: AVATAR_SIZE / 2,
    backgroundColor: COLORS.primarySoft,
    marginBottom: 12,
  },
  avatarFallback: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarInitials: {
    fontSize: 32,
    fontWeight: '700',
    color: COLORS.primary,
  },
  name: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.text,
    textAlign: 'center',
    writingDirection: 'rtl',
    lineHeight: 30, // Arabic glyphs need extra vertical room
  },
  phoneRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  phone: {
    fontSize: 15,
    color: COLORS.textMuted,
    marginStart: 6,
    writingDirection: 'ltr',
    fontVariant: ['tabular-nums'],
  },

  // Settings
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textMuted,
    textAlign: TEXT_START,
    writingDirection: 'rtl',
    marginBottom: 8,
    paddingHorizontal: 4,
  },
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    overflow: 'hidden',
    marginBottom: 24,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingStart: 16,
    minHeight: 56,
  },
  rowPressed: {
    backgroundColor: COLORS.background,
  },
  iconWrap: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: COLORS.primarySoft,
    alignItems: 'center',
    justifyContent: 'center',
    marginEnd: 12,
  },
  rowBody: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'stretch',
    paddingEnd: 16,
  },
  rowDivider: {
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: COLORS.separator,
  },
  rowLabel: {
    flex: 1,
    fontSize: 16,
    color: COLORS.text,
    textAlign: TEXT_START,
    writingDirection: 'rtl',
    lineHeight: 24,
  },

  // Logout
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.dangerSoft,
    borderRadius: 14,
    minHeight: 52,
    paddingHorizontal: 16,
  },
  logoutPressed: {
    opacity: 0.8,
  },
  logoutText: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.danger,
    marginStart: 8,
    writingDirection: 'rtl',
  },
  // Ionicons' log-out arrow points right (LTR "exit"); mirror it for RTL.
  flipForRtl: {
    transform: [{ scaleX: -1 }],
  },

  version: {
    marginTop: 16,
    fontSize: 12,
    color: COLORS.chevron,
    textAlign: 'center',
    writingDirection: 'rtl',
  },
});

export default ProfileScreen;
