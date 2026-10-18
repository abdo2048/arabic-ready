/**
 * ProfileScreen.tsx — Arabic (RTL) profile screen for Expo / React Native.
 *
 * Dependencies:
 *   npx expo install @expo/vector-icons expo-updates \
 *     @expo-google-fonts/ibm-plex-sans-arabic expo-font
 *
 * app.json (recommended, so the native layout direction is RTL from the first launch):
 *   "expo": { "extra": { "supportsRTL": true, "forcesRTL": true } }
 *
 * Layout uses logical props only (marginStart / paddingEnd / start ...) and plain
 * flexDirection: 'row', which flips automatically when I18nManager.isRTL is true.
 */
import React from "react";
import {
  Alert,
  I18nManager,
  Image,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import * as Updates from "expo-updates";
import {
  useFonts,
  IBMPlexSansArabic_400Regular,
  IBMPlexSansArabic_500Medium,
  IBMPlexSansArabic_700Bold,
} from "@expo-google-fonts/ibm-plex-sans-arabic";

// --- Force RTL once at the app root. forceRTL only takes effect after a reload. ---
I18nManager.allowRTL(true);
if (!I18nManager.isRTL) {
  I18nManager.forceRTL(true);
  Updates.reloadAsync().catch(() => {
    /* In dev without expo-updates, reload the app manually once. */
  });
}

// Directional icons (chevrons, logout door-arrow) must be mirrored in RTL.
const mirrorInRTL = { transform: [{ scaleX: I18nManager.isRTL ? -1 : 1 }] };

// LRI … PDI: isolates an LTR island (phone number) inside RTL text.
const ltr = (s: string) => `⁦${s}⁩`;

type IconName = React.ComponentProps<typeof Ionicons>["name"];

type SettingsItem = {
  key: string;
  icon: IconName;
  label: string;
  onPress: () => void;
};

const user = {
  name: "سارة العتيبي",
  phone: "+966 50 123 4567",
  avatar: "https://i.pravatar.cc/300?img=47",
};

const settings: SettingsItem[] = [
  { key: "account", icon: "person-outline", label: "معلومات الحساب", onPress: () => {} },
  { key: "notifications", icon: "notifications-outline", label: "الإشعارات", onPress: () => {} },
  { key: "privacy", icon: "lock-closed-outline", label: "الخصوصية والأمان", onPress: () => {} },
  { key: "language", icon: "language-outline", label: "اللغة", onPress: () => {} },
  { key: "payment", icon: "card-outline", label: "طرق الدفع", onPress: () => {} },
  { key: "help", icon: "help-circle-outline", label: "المساعدة والدعم", onPress: () => {} },
];

function SettingsRow({ item, isLast }: { item: SettingsItem; isLast: boolean }) {
  return (
    <Pressable
      onPress={item.onPress}
      accessibilityRole="button"
      accessibilityLabel={item.label}
      style={({ pressed }) => [
        styles.row,
        !isLast && styles.rowDivider,
        pressed && styles.rowPressed,
      ]}
    >
      <View style={styles.rowIconWrap}>
        {/* Non-directional icons: not mirrored */}
        <Ionicons name={item.icon} size={20} color={COLORS.primary} />
      </View>
      <Text style={styles.rowLabel} numberOfLines={1}>
        {item.label}
      </Text>
      {/* "Forward" chevron: points left in RTL */}
      <Ionicons
        name="chevron-forward"
        size={18}
        color={COLORS.muted}
        style={mirrorInRTL}
      />
    </Pressable>
  );
}

export default function ProfileScreen() {
  const [fontsLoaded] = useFonts({
    IBMPlexSansArabic_400Regular,
    IBMPlexSansArabic_500Medium,
    IBMPlexSansArabic_700Bold,
  });

  if (!fontsLoaded) return null;

  const confirmLogout = () =>
    Alert.alert("تسجيل الخروج", "هل تريد تسجيل الخروج من حسابك؟", [
      { text: "إلغاء", style: "cancel" },
      { text: "سجّل الخروج", style: "destructive", onPress: () => {} },
    ]);

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>الملف الشخصي</Text>

        {/* Header: avatar, name, phone */}
        <View style={styles.header}>
          <Image source={{ uri: user.avatar }} style={styles.avatar} accessibilityLabel="الصورة الشخصية" />
          <Text style={styles.name}>{user.name}</Text>
          {/* Phone number stays LTR: isolated + writingDirection ltr */}
          <Text style={styles.phone} accessibilityLabel={`رقم الجوال ${user.phone}`}>
            {ltr(user.phone)}
          </Text>
        </View>

        {/* Settings list */}
        <Text style={styles.sectionTitle}>الإعدادات</Text>
        <View style={styles.card}>
          {settings.map((item, i) => (
            <SettingsRow key={item.key} item={item} isLast={i === settings.length - 1} />
          ))}
        </View>

        {/* Logout */}
        <Pressable
          onPress={confirmLogout}
          accessibilityRole="button"
          accessibilityLabel="سجّل الخروج"
          style={({ pressed }) => [styles.logout, pressed && styles.logoutPressed]}
        >
          {/* Logout door-arrow is directional: mirrored in RTL */}
          <Ionicons name="log-out-outline" size={20} color={COLORS.danger} style={mirrorInRTL} />
          <Text style={styles.logoutText}>سجّل الخروج</Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

const COLORS = {
  bg: "#F5F6F8",
  card: "#FFFFFF",
  text: "#1A1D23",
  muted: "#8A919E",
  divider: "#ECEEF1",
  primary: "#0F766E",
  primarySoft: "#E6F4F2",
  danger: "#C62828",
  dangerSoft: "#FDECEC",
};

const FONT = {
  regular: "IBMPlexSansArabic_400Regular",
  medium: "IBMPlexSansArabic_500Medium",
  bold: "IBMPlexSansArabic_700Bold",
};

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: COLORS.bg,
  },
  content: {
    paddingHorizontal: 16,
    paddingBottom: 32,
  },
  title: {
    fontFamily: FONT.bold,
    fontSize: 22,
    lineHeight: 34,
    color: COLORS.text,
    marginTop: 12,
    writingDirection: "rtl",
  },
  header: {
    alignItems: "center",
    paddingVertical: 24,
  },
  avatar: {
    width: 104,
    height: 104,
    borderRadius: 52,
    backgroundColor: COLORS.divider,
    marginBottom: 12,
  },
  name: {
    fontFamily: FONT.bold,
    fontSize: 20,
    lineHeight: 32,
    color: COLORS.text,
    textAlign: "center",
    writingDirection: "rtl",
  },
  phone: {
    fontFamily: FONT.regular,
    fontSize: 15,
    lineHeight: 24,
    color: COLORS.muted,
    marginTop: 2,
    textAlign: "center",
    writingDirection: "ltr", // phone numbers always read left-to-right
  },
  sectionTitle: {
    fontFamily: FONT.medium,
    fontSize: 14,
    lineHeight: 22,
    color: COLORS.muted,
    marginBottom: 8,
    paddingHorizontal: 4,
    writingDirection: "rtl",
  },
  card: {
    backgroundColor: COLORS.card,
    borderRadius: 14,
    overflow: "hidden",
  },
  row: {
    flexDirection: "row", // flips automatically under RTL: icon on the right, chevron on the left
    alignItems: "center",
    minHeight: 56,
    paddingVertical: 10,
    paddingStart: 14,
    paddingEnd: 12,
    backgroundColor: COLORS.card,
  },
  rowDivider: {
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: COLORS.divider,
  },
  rowPressed: {
    backgroundColor: COLORS.bg,
  },
  rowIconWrap: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: COLORS.primarySoft,
    alignItems: "center",
    justifyContent: "center",
    marginEnd: 12,
  },
  rowLabel: {
    flex: 1,
    fontFamily: FONT.medium,
    fontSize: 16,
    lineHeight: 26,
    color: COLORS.text,
    writingDirection: "rtl",
  },
  logout: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    marginTop: 24,
    minHeight: 52,
    borderRadius: 14,
    backgroundColor: COLORS.dangerSoft,
  },
  logoutPressed: {
    opacity: 0.8,
  },
  logoutText: {
    fontFamily: FONT.bold,
    fontSize: 16,
    lineHeight: 26,
    color: COLORS.danger,
    writingDirection: "rtl",
  },
});
