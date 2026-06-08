import { MaterialIcons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useState } from 'react';
import {
  Alert,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { RegisterFormErrors, validateRegisterForm } from '@/schemas/auth';
import { api } from '@/services/api';

const BRAND_BLUE = '#0058BC';

export default function RegisterScreen() {
  const router = useRouter();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<RegisterFormErrors>({});

  const onRegister = async () => {
    const validationErrors = validateRegisterForm({
      fullName,
      email,
      password,
      confirmPassword,
    });

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setErrors({});

    try {
      setLoading(true);
      const user = await api.register({
        email: email.trim(),
        password,
        confirm_password: confirmPassword,
        full_name: fullName.trim() || undefined,
      });
      console.log('Người dùng đã đăng ký:', user);
      Alert.alert('Đăng ký thành công', `Tài khoản ${user.email} đã được tạo`);
      router.replace('/(tabs)/login');
    } catch (error) {
      console.log('Lỗi đăng ký:', error);
      const message = error instanceof Error ? error.message : 'Đăng ký thất bại';
      Alert.alert('Đăng ký thất bại', message);
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
          <Text style={styles.brandSubtitle}>Tạo tài khoản mới</Text>
        </View>

        <View style={styles.card}>
          <View style={styles.fieldWrap}>
            <Text style={styles.fieldLabel}>Họ và tên</Text>
            <View style={styles.inputWrap}>
              <MaterialIcons name="person" size={18} color={BRAND_BLUE} style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder="Nguyễn Văn A"
                placeholderTextColor="#9CA3AF"
                value={fullName}
                onChangeText={(value) => {
                  setFullName(value);
                  if (errors.fullName) {
                    setErrors((prev) => ({ ...prev, fullName: undefined }));
                  }
                }}
              />
            </View>
            {errors.fullName ? <Text style={styles.errorText}>{errors.fullName}</Text> : null}
          </View>

          <View style={styles.fieldWrap}>
            <Text style={styles.fieldLabel}>Địa chỉ email</Text>
            <View style={styles.inputWrap}>
              <MaterialIcons name="mail" size={18} color={BRAND_BLUE} style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder="ten@congty.vn"
                placeholderTextColor="#9CA3AF"
                value={email}
                onChangeText={(value) => {
                  setEmail(value);
                  if (errors.email) {
                    setErrors((prev) => ({ ...prev, email: undefined }));
                  }
                }}
                keyboardType="email-address"
                autoCapitalize="none"
              />
            </View>
            {errors.email ? <Text style={styles.errorText}>{errors.email}</Text> : null}
          </View>

          <View style={styles.fieldWrap}>
            <Text style={styles.fieldLabel}>Mật khẩu</Text>
            <View style={styles.inputWrap}>
              <MaterialIcons name="lock" size={18} color={BRAND_BLUE} style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder="••••••••"
                placeholderTextColor="#9CA3AF"
                value={password}
                onChangeText={(value) => {
                  setPassword(value);
                  if (errors.password || errors.confirmPassword) {
                    setErrors((prev) => ({
                      ...prev,
                      password: undefined,
                      confirmPassword: undefined,
                    }));
                  }
                }}
                secureTextEntry
              />
            </View>
            {errors.password ? <Text style={styles.errorText}>{errors.password}</Text> : null}
          </View>

          <View style={styles.fieldWrap}>
            <Text style={styles.fieldLabel}>Xác nhận mật khẩu</Text>
            <View style={styles.inputWrap}>
              <MaterialIcons
                name="verified-user"
                size={18}
                color={BRAND_BLUE}
                style={styles.inputIcon}
              />
              <TextInput
                style={styles.input}
                placeholder="••••••••"
                placeholderTextColor="#9CA3AF"
                value={confirmPassword}
                onChangeText={(value) => {
                  setConfirmPassword(value);
                  if (errors.confirmPassword) {
                    setErrors((prev) => ({ ...prev, confirmPassword: undefined }));
                  }
                }}
                secureTextEntry
              />
            </View>
            {errors.confirmPassword ? <Text style={styles.errorText}>{errors.confirmPassword}</Text> : null}
          </View>

          <Pressable style={styles.loginButton} onPress={onRegister} disabled={loading}>
            <Text style={styles.loginButtonText}>{loading ? 'Đang xử lý...' : 'Đăng ký'}</Text>
            <MaterialIcons name="arrow-forward" size={19} color="#FFFFFF" />
          </Pressable>

          <View style={styles.secureLineRow}>
            <View style={styles.secureLine} />
            <Text style={styles.secureText}>Truy cập bảo mật</Text>
            <View style={styles.secureLine} />
          </View>

          <Pressable style={styles.ssoButton}>
            <MaterialIcons name="fingerprint" size={20} color="#111827" />
            <Text style={styles.ssoText}>Đăng ký nhanh</Text>
          </Pressable>
        </View>

        <View style={styles.footerRow}>
          <Text style={styles.footerText}>Đã có tài khoản?</Text>
          <Pressable onPress={() => router.push('/(tabs)/login')}>
            <Text style={styles.footerLink}>Đăng nhập</Text>
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
  fieldLabel: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0A0A0A',
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
  errorText: {
    marginTop: -2,
    color: '#DC2626',
    fontSize: 12,
    fontWeight: '600',
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
