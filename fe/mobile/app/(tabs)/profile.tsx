import useAuth from '@/hooks/use-auth';
import { MaterialIcons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useState } from 'react';
import {
  Image,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  View,
} from 'react-native';

const BRAND_BLUE = '#0058BC';

function SettingRow({
  icon,
  title,
  subtitle,
  right,
  onPress,
}: {
  icon: keyof typeof MaterialIcons.glyphMap;
  title: string;
  subtitle?: string;
  right?: React.ReactNode;
  onPress?: () => void;
}) {
  return (
    <Pressable onPress={onPress} style={styles.settingRow}>
      <View style={styles.settingLeft}>
        <View style={styles.settingIconWrap}>
          <MaterialIcons name={icon} size={20} color={BRAND_BLUE} />
        </View>
        <View style={styles.settingTextWrap}>
          <Text style={styles.settingTitle}>{title}</Text>
          {subtitle ? <Text style={styles.settingSubtitle}>{subtitle}</Text> : null}
        </View>
      </View>
      {right}
    </Pressable>
  );
}

export default function ProfileScreen() {
  const router = useRouter();
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const { user } = useAuth();

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <View style={styles.brandRow}>
          <View style={styles.brandIconWrap}>
            <MaterialIcons name="sensors" size={20} color={BRAND_BLUE} />
          </View>
          <Text style={styles.brandText}>Trung tâm giám sát</Text>
        </View>
        <Image
          source={{
            uri: 'https://lh3.googleusercontent.com/aida-public/AB6AXuArywmAnwFZz4yyE-xjsDoSlA-MGwgg1OJWLd5XNAedZ0mWo8y_vNSIDVZ_i58lNpLqAX4R1mMXy7C2OJUoGmonYiCElYB4uYy-lAibPcXTW7AwJN89uOJff28IgkevvvJ-B-MrCk0k30s77klKGmwafO2Ja3U90nZZzg5YIoisTXcylzQ0VZdLeBpCURmKeK2Avci7u4jfNZ5lYpWgPkqwCTQ_7BG4V-_xfU7ZSr4mpyQbj4onUoFYYOfQjv4r2KY87izSgqepUIp1',
          }}
          style={styles.topAvatar}
        />
      </View>

      <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
        <View style={styles.profileHeader}>
          <View style={styles.profilePhotoWrap}>
            <Image
              source={{
                uri: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBaHbgSFTmpUrW4mB83PmCfow5t4mEX0c7VuZ9y7h8PdajqHGYarL1kZTzLsKFYettLQ8b2Cczwrw0Os7anPk0K50j3cOxtOeDKz3wU4oNwdZYsCtWSuNpGVLnDI3IfpvHXF7niIs1dx-kI_2pArM2VYjaX9XP3MunL0XX3L3pXmBn7zzkw83QWDCroa8P7dZBcd76O5Bq4lj6lb8YG3xrxXmJlQw4VBr9__4vb9kmkievLfK_f6wtdRDOr335tsF5A13fm6K3m9K-s',
              }}
              style={styles.profileAvatar}
            />
            <Pressable style={styles.editFab}>
              <MaterialIcons name="edit" size={14} color="#FFFFFF" />
            </Pressable>
          </View>
          <Text style={styles.profileName}>{user?.email ? user.email.charAt(0).toUpperCase(): ''}</Text>
          <Text style={styles.profileEmail}>{user?.email}</Text>
        </View>

       {
          !user && (
             <View style={styles.authActions}>
          <Pressable onPress={() => router.push('/(tabs)/login')} style={styles.authButtonPrimary}>
            <MaterialIcons name="login" size={16} color="#FFFFFF" />
            <Text style={styles.authButtonPrimaryText}>Đăng nhập</Text>
          </Pressable>
          <Pressable onPress={() => router.push('/(tabs)/register')} style={styles.authButtonSecondary}>
            <MaterialIcons name="person-add" size={16} color="#0F172A" />
            <Text style={styles.authButtonSecondaryText}>Đăng ký</Text>
          </Pressable>
        </View>
          )
       }
        <View style={styles.insightCard}>
          <View style={styles.insightHead}>
            <MaterialIcons name="auto-awesome" size={18} color={BRAND_BLUE} />
            <Text style={styles.insightLabel}>Thông tin hệ thống</Text>
          </View>
          <Text style={styles.insightText}>
            Bảo mật tài khoản của bạn hiện ở mức 94%. Bật xác thực sinh trắc học có thể cải thiện
            điểm Observatory của bạn lên 100%.
          </Text>
        </View>

        <View style={styles.groupWrap}>
          <Text style={styles.groupTitle}>Cài đặt tài khoản</Text>
          <View style={styles.groupCard}>
            <SettingRow
              icon="notifications"
              title="Thông báo"
              subtitle="Cảnh báo, cập nhật và hoạt động"
              right={
                <Switch
                  value={notificationsEnabled}
                  onValueChange={setNotificationsEnabled}
                  trackColor={{ false: '#E5E7EB', true: '#0058BC' }}
                  thumbColor="#FFFFFF"
                />
              }
            />
            <SettingRow
              icon="dark-mode"
              title="Giao diện ứng dụng"
              subtitle="Hệ thống (chế độ sáng)"
              right={<MaterialIcons name="chevron-right" size={20} color="#94A3B8" />}
            />
            <SettingRow
              icon="straighten"
              title="Đơn vị"
              subtitle="Hệ mét (Độ C, Mét)"
              right={<MaterialIcons name="chevron-right" size={20} color="#94A3B8" />}
            />
          </View>
        </View>

        <View style={styles.groupWrap}>
          <Text style={styles.groupTitle}>Hỗ trợ và quyền riêng tư</Text>
          <View style={styles.groupCard}>
            <SettingRow
              icon="security"
              title="Chính sách bảo mật"
              right={<MaterialIcons name="open-in-new" size={18} color="#94A3B8" />}
            />
            <SettingRow
              icon="help"
              title="Trung tâm trợ giúp"
              right={<MaterialIcons name="chevron-right" size={20} color="#94A3B8" />}
            />
          </View>
        </View>

        <Pressable style={styles.logoutButton}>
          <MaterialIcons name="logout" size={18} color="#FFFFFF" />
          <Text style={styles.logoutText}>Đăng xuất</Text>
        </Pressable>

        <Text style={styles.version}>PHIÊN BẢN 2.4.0 (OBSERVATORY-STABLE)</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  header: {
    height: 64,
    paddingHorizontal: 18,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'rgba(255,255,255,0.96)',
  },
  brandRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  brandIconWrap: {
    width: 34,
    height: 34,
    borderRadius: 12,
    backgroundColor: '#EFF6FF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  brandText: {
    fontSize: 20,
    fontWeight: '800',
    letterSpacing: -0.6,
    color: '#0F172A',
  },
  topAvatar: {
    width: 38,
    height: 38,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  container: {
    paddingHorizontal: 18,
    paddingTop: 18,
    paddingBottom: 28,
    gap: 16,
  },
  profileHeader: {
    alignItems: 'center',
    marginBottom: 4,
  },
  profilePhotoWrap: {
    position: 'relative',
    marginBottom: 12,
  },
  profileAvatar: {
    width: 108,
    height: 108,
    borderRadius: 999,
    borderWidth: 2,
    borderColor: '#FFFFFF',
  },
  editFab: {
    position: 'absolute',
    right: 2,
    bottom: 2,
    width: 28,
    height: 28,
    borderRadius: 999,
    backgroundColor: '#0A0A0A',
    alignItems: 'center',
    justifyContent: 'center',
  },
  profileName: {
    fontSize: 27,
    fontWeight: '800',
    color: '#0F172A',
    letterSpacing: -0.7,
  },
  profileEmail: {
    color: BRAND_BLUE,
    fontSize: 14,
    fontWeight: '600',
  },
  authActions: {
    flexDirection: 'row',
    gap: 10,
  },
  authButtonPrimary: {
    flex: 1,
    height: 44,
    borderRadius: 12,
    backgroundColor: '#0A0A0A',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  authButtonPrimaryText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 14,
  },
  authButtonSecondary: {
    flex: 1,
    height: 44,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    backgroundColor: '#FFFFFF',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  authButtonSecondaryText: {
    color: '#0F172A',
    fontWeight: '700',
    fontSize: 14,
  },
  insightCard: {
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#E0E0E0',
    borderLeftWidth: 4,
    borderLeftColor: BRAND_BLUE,
    backgroundColor: '#FFFFFF',
    padding: 14,
    gap: 6,
  },
  insightHead: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  insightLabel: {
    color: BRAND_BLUE,
    fontSize: 10,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  insightText: {
    color: '#64748B',
    lineHeight: 20,
    fontSize: 13,
  },
  groupWrap: {
    gap: 8,
  },
  groupTitle: {
    paddingHorizontal: 4,
    fontSize: 11,
    fontWeight: '800',
    color: '#6B7280',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  groupCard: {
    borderWidth: 1,
    borderColor: '#F1F5F9',
    borderRadius: 14,
    overflow: 'hidden',
    backgroundColor: '#FFFFFF',
  },
  settingRow: {
    minHeight: 76,
    paddingHorizontal: 14,
    paddingVertical: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderBottomWidth: 1,
    borderBottomColor: '#F8FAFC',
  },
  settingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  settingIconWrap: {
    width: 40,
    height: 40,
    borderRadius: 10,
    backgroundColor: '#EFF6FF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  settingTextWrap: {
    flex: 1,
    gap: 2,
  },
  settingTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#111827',
  },
  settingSubtitle: {
    fontSize: 12,
    color: '#6B7280',
  },
  logoutButton: {
    marginTop: 4,
    minHeight: 50,
    borderRadius: 12,
    backgroundColor: '#0A0A0A',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  logoutText: {
    color: '#FFFFFF',
    fontWeight: '800',
    fontSize: 15,
  },
  version: {
    textAlign: 'center',
    marginTop: 10,
    fontSize: 10,
    color: '#94A3B8',
    fontWeight: '700',
    letterSpacing: 0.7,
  },
});
