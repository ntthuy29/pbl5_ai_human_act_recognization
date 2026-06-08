import { Tabs } from 'expo-router';
import { Redirect, useSegments } from 'expo-router';
import React from 'react';

import { HapticTab } from '@/components/haptic-tab';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { Colors } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import useAuth from '@/hooks/use-auth';

export default function TabLayout() {
  const colorScheme = useColorScheme();
  const segments = useSegments();
  const { user, loading } = useAuth();

  if (loading) {
    return null;
  }

  const isAuthScreen = segments[1] === 'login' || segments[1] === 'register';

  if (!user && !isAuthScreen) {
    return <Redirect href="/(tabs)/login" />;
  }

  if (user && isAuthScreen) {
    return <Redirect href="/(tabs)/home" />;
  }

  return (
    <Tabs
      initialRouteName="home"
      screenOptions={{
        tabBarActiveTintColor: Colors[colorScheme ?? 'light'].tint,
        tabBarInactiveTintColor: '#8A95A7',
        headerShown: false,
        tabBarButton: HapticTab,
        tabBarStyle: {
          height: 66,
          paddingTop: 6,
          paddingBottom: 8,
        },
      }}>
      <Tabs.Screen
        name="home"
        options={{
          title: 'Trang chủ',
          tabBarIcon: ({ color }) => <IconSymbol size={28} name="house.fill" color={color} />,
        }}
      />
      <Tabs.Screen
        name="history"
        options={{
          title: 'Lịch sử',
          tabBarIcon: ({ color }) => <IconSymbol size={28} name="clock.fill" color={color} />,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Hồ sơ',
          tabBarIcon: ({ color }) => <IconSymbol size={28} name="person.circle.fill" color={color} />,
        }}
      />
      <Tabs.Screen
        name="login"
        options={{
          href: null,
        }}
      />
      <Tabs.Screen
        name="register"
        options={{
          href: null,
        }}
      />
     
    </Tabs>
    
  );
}
