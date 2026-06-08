import useAuth from '@/hooks/use-auth';
import { LoginPayload } from '@/services/type';
import { MaterialIcons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useState } from 'react';
import {
  Alert,
  Image,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { api } from '@/services/api';

const BRAND_BLUE = '#0058BC';

export default function LoginScreen() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { user, setUser, loading: authLoading, setLoading: setAuthLoading } = useAuth();
  

  const onLogin = async () => {
    if (!email.trim() || !password) {
      Alert.alert('Thông báo', 'Vui lòng nhập email và mật khẩu');
      return;
    }

    try {
      setLoading(true);
      const payload: LoginPayload = {
        email: email.trim(),
        password,
      };
        const user: any = await api.login(payload);
      Alert.alert('Đăng nhập thành công', `Xin chào ${user.email}!`);
      setUser(user);
      setLoading(false);

      console.log('Logged in user:', user);
      router.replace('/(tabs)/home');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Đăng nhập thất bại';
      Alert.alert('Đăng nhập thất bại', message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.bgOrbTop} />
      <View style={styles.bgOrbBottom} />

      <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
        <View style={styles.identityBlock}>
          <View style={styles.logoBox}>
            <MaterialIcons name="monitor" size={36} color={BRAND_BLUE} />
          </View>
          <Text style={styles.brandTitle}>Hệ thống thông minh</Text>
          <Text style={styles.brandSubtitle}>Phát hiện sự hiện diện của con người</Text>
        </View>

        <View style={styles.card}>
          <View style={styles.fieldWrap}>
            <Text style={styles.fieldLabel}>Địa chỉ email</Text>
            <View style={styles.inputWrap}>
              <MaterialIcons name="mail" size={18} color={BRAND_BLUE} style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder="ten@congty.vn"
                placeholderTextColor="#9CA3AF"
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
              />
            </View>
          </View>

          <View style={styles.fieldWrap}>
            <View style={styles.fieldHeadRow}>
              <Text style={styles.fieldLabel}>Mật khẩu</Text>
              <Pressable>
                <Text style={styles.forgotLink}>Quên?</Text>
              </Pressable>
            </View>
            <View style={styles.inputWrap}>
              <MaterialIcons name="lock" size={18} color={BRAND_BLUE} style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder="••••••••"
                placeholderTextColor="#9CA3AF"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
              />
            </View>
          </View>
      { !user &&
          <Pressable style={styles.loginButton} onPress={onLogin} disabled={loading}>
                  <Text style={styles.loginButtonText}>{loading ? 'Đang xử lý...' : 'Đăng nhập'}</Text>
            <MaterialIcons name="arrow-forward" size={19} color="#FFFFFF" />
          </Pressable>
}

          <View style={styles.secureLineRow}>
            <View style={styles.secureLine} />
            <Text style={styles.secureText}>Truy cập bảo mật</Text>
            <View style={styles.secureLine} />
          </View>

          <Pressable style={styles.ssoButton}>
            <Image
              source={{
                uri: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCwJt559YLsQPsf0b7bf0B142ZfXNR-eFATTxJm3TCvsdrhKwDcBePDmWaWpTI9UKnqm7T_ii2r4TEBJqLtzNLNIlF3pp0CZtKQjF0TK02cXobrw-NUz_ejvfgtZyxs--zEA2Z7AfwReg1od9Lz6SaDhH1aiHP9fRb1NiyuybUryV1-Nmf1BT6TFIDcIYDSl5qvID7DKRrnn_SRa7E_9bUEPcW84an_e3XWvc1Pp6K2AMbE2uzHmzDUHGwja2Mr1zbwj_NlyUf-pjcY',
              }}
              style={styles.ssoIcon}
            />
            <Text style={styles.ssoText}>Đăng nhập với SSO</Text>
          </Pressable>
        </View>

        <View style={styles.footerRow}>
          <Text style={styles.footerText}>Chưa có tài khoản?</Text>
          <Pressable onPress={() => router.push('/(tabs)/register')}>
            <Text style={styles.footerLink}>Đăng ký</Text>
          </Pressable>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  container: {
    minHeight: '100%',
    paddingHorizontal: 20,
    paddingTop: 26,
    paddingBottom: 24,
    justifyContent: 'center',
    gap: 20,
  },
  bgOrbTop: {
    position: 'absolute',
    top: -110,
    right: -65,
    width: 220,
    height: 220,
    borderRadius: 999,
    backgroundColor: '#EEF4FF',
  },
  bgOrbBottom: {
    position: 'absolute',
    bottom: -120,
    left: -80,
    width: 250,
    height: 250,
    borderRadius: 999,
    backgroundColor: '#F6F9FF',
  },
  identityBlock: {
    alignItems: 'center',
    gap: 8,
  },
  logoBox: {
    width: 64,
    height: 64,
    borderRadius: 14,
    backgroundColor: '#0A0A0A',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 2,
  },
  brandTitle: {
    fontSize: 31,
    fontWeight: '800',
    letterSpacing: -0.8,
    color: '#020617',
  },
  brandSubtitle: {
    fontSize: 14,
    fontWeight: '600',
    color: BRAND_BLUE,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    paddingHorizontal: 18,
    paddingVertical: 20,
    gap: 16,
    shadowColor: '#000000',
    shadowOpacity: 0.05,
    shadowRadius: 14,
    shadowOffset: { width: 0, height: 8 },
    elevation: 2,
  },
  fieldWrap: {
    gap: 8,
  },
  fieldHeadRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  fieldLabel: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0A0A0A',
  },
  forgotLink: {
    fontSize: 12,
    fontWeight: '700',
    color: BRAND_BLUE,
  },
  inputWrap: {
    minHeight: 52,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    backgroundColor: '#F8F9FA',
    justifyContent: 'center',
  },
  inputIcon: {
    position: 'absolute',
    left: 12,
    top: 16,
  },
  input: {
    fontSize: 15,
    color: '#111827',
    paddingLeft: 40,
    paddingRight: 12,
    paddingVertical: 12,
  },
  loginButton: {
    minHeight: 54,
    borderRadius: 12,
    backgroundColor: '#0A0A0A',
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 7,
    marginTop: 2,
  },
  loginButtonText: {
    fontSize: 16,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  secureLineRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginTop: 4,
  },
  secureLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#E5E7EB',
  },
  secureText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#9CA3AF',
    textTransform: 'uppercase',
    letterSpacing: 0.9,
  },
  ssoButton: {
    minHeight: 50,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    backgroundColor: '#F8F9FA',
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 10,
  },
  ssoIcon: {
    width: 20,
    height: 20,
    borderRadius: 10,
  },
  ssoText: {
    color: '#0F172A',
    fontSize: 14,
    fontWeight: '700',
  },
  footerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  footerText: {
    color: '#6B7280',
    fontSize: 14,
  },
  footerLink: {
    color: BRAND_BLUE,
    fontSize: 14,
    fontWeight: '800',
  },
});
