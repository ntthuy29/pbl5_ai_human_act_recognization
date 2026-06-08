import useAuth from '@/hooks/use-auth';
import { MaterialIcons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useEffect, useRef, useState } from 'react';

import { API_BASE_URL, api } from '@/services/api';
import { PredictionData, StatusData } from '@/services/type';
import {
    ActivityIndicator,
    Alert,
    Animated,
    Pressable,
    SafeAreaView,
    ScrollView,
    StyleSheet,
    Text,
	type DimensionValue,
    View,
} from 'react-native';

const BRAND_BLUE = '#0058BC';
const DEMO_MODE = String(process.env.EXPO_PUBLIC_DEMO_MODE ?? '').trim().toLowerCase() === 'true';

function formatPercent(value: number | null | undefined, fractionDigits = 1, fallback = '---'): string {
	if (value === null || value === undefined || Number.isNaN(value)) {
		return fallback;
	}

	return value.toFixed(fractionDigits);
}

function formatPercentWidth(value: number | null | undefined): DimensionValue {
	const numericValue = value === null || value === undefined || Number.isNaN(value)
		? 0
		: Math.min(100, Math.max(0, value));

	return `${numericValue}%`;
}

function getDisplayConfidence(actualConfidence: number | null | undefined): number | null {
	if (actualConfidence === null || actualConfidence === undefined) {
		return null;
	}

	const actualPercent = actualConfidence * 100;
	if (!DEMO_MODE || actualPercent <= 80) {
		return actualPercent;
	}

	return 70 + Math.random() * 10;
}

export default function HomeScreen() {
	const router = useRouter();
	const fadeIn = useRef(new Animated.Value(0)).current;
	const slideIn = useRef(new Animated.Value(18)).current;
	const [status, setStatus] = useState<StatusData | null>(null);
	const [latest, setLatest] = useState<PredictionData | null>(null);
	const [displayConfidence, setDisplayConfidence] = useState<number | null>(null);
	const [loading, setLoading] = useState(true);
	const [liveConnected, setLiveConnected] = useState(false);
	
	const { user } = useAuth();
	const hasEsp32Connection = Boolean(status?.esp32_1_connected || status?.esp32_2_connected);
	const showNoEsp32DataNotice = Boolean(status?.monitoring && !hasEsp32Connection && !latest);
	const showWaitingPredictionNotice = Boolean(status?.monitoring && hasEsp32Connection && !latest);
	const livePrediction = status?.live_prediction;
	const udpStats = status?.udp;
	const presenceLabel = latest?.presence === 'person'
		? 'CÓ NGƯỜI'
		: latest?.presence === 'no_person'
			? 'KHÔNG CÓ NGƯỜI'
			: latest?.presence ?? 'ĐANG CHỜ';
	const presenceTone = latest?.presence === 'person' ? styles.predictionPositive : styles.predictionNeutral;

	useEffect(() => {
		setDisplayConfidence(getDisplayConfidence(latest?.confidence));
	}, [latest?.confidence, latest?.timestamp]);

	const fetchDashboard = async (silent = false) => {
		try {
			const statusData = await api.getStatus();
			setStatus(statusData);
			if (statusData.latest_prediction) {
				setLatest(statusData.latest_prediction);
			}
		} catch (error) {
			if (!silent) {
				const message = error instanceof Error ? error.message : 'Không thể tải dữ liệu';
				Alert.alert('Lỗi kết nối API', message);
			}
		} finally {
			if (!silent) {
				setLoading(false);
			}
		}
	};

	const connectPredictionStream = () => {
		const wsUrl = API_BASE_URL.replace(/^http/, 'ws').replace(/\/$/, '') + '/ws/predictions';
		const socket = new WebSocket(wsUrl);

		socket.onopen = () => {
			setLiveConnected(true);
		};

		socket.onmessage = (event) => {
			try {
				const message = JSON.parse(event.data as string) as { type?: string; data?: PredictionData };
				if (message.type === 'latest_prediction' && message.data) {
					setLatest(message.data);
				}
			} catch (error) {
				console.log('Tải dữ liệu prediction từ websocket không hợp lệ', error);
			}
		};

		socket.onerror = () => {
			setLiveConnected(false);
		};

		socket.onclose = () => {
			setLiveConnected(false);
		};

		return socket;
	};

	const onToggleMonitoring = async () => {
		if (!status) {
			console.log('Trạng thái chưa có, không thể đổi chế độ giám sát');
			return;
		}

		if (!user) {
			Alert.alert('Yêu cầu đăng nhập', 'Bạn cần đăng nhập để bắt đầu hoặc dừng giám sát.');
			router.push('/(tabs)/login');
			return;
		}

		try {
			if (status.monitoring) {
				console.log('Đang dừng giám sát...');
				await api.stopMonitoring();
			} else {
				console.log('Đang bắt đầu giám sát...');
				await api.startMonitoring();
			}
			await fetchDashboard();
		} catch (error) {
			const message = error instanceof Error ? error.message : 'Không thể cập nhật giám sát';
			Alert.alert('Lỗi', message);
		}
	};

	useEffect(() => {
		Animated.parallel([
			Animated.timing(fadeIn, {
				toValue: 1,
				duration: 450,
				useNativeDriver: true,
			}),
			Animated.spring(slideIn, {
				toValue: 0,
				damping: 16,
				stiffness: 120,
				useNativeDriver: true,
			}),
		]).start();
		fetchDashboard(false);
		const socket = connectPredictionStream();

		const pollId = setInterval(() => {
			fetchDashboard(true);
		}, 2000);

		return () => {
			clearInterval(pollId);
			socket.close();
		};
	}, [fadeIn, slideIn]);
	

	return (
		<SafeAreaView style={styles.safeArea}>
			<View style={styles.bgGradient} />
			<View style={styles.bgOrbTop} />
			<View style={styles.bgOrbBottom} />

			<View style={styles.header}>
				<View style={styles.brandRow}>
					<View style={styles.brandIconWrap}>
						<MaterialIcons name="sensors" size={20} color="#121212" />
					</View>
					<Text style={styles.brandText}>Trung tâm giám sát</Text>
				</View>

				<Pressable onPress={() => router.push('/(tabs)/profile')} style={styles.avatar}>
					<MaterialIcons name="person" size={20} color="#64748B" />
				</Pressable>
			</View>

			<Animated.View
				style={[
					styles.animatedArea,
					{
						opacity: fadeIn,
						transform: [{ translateY: slideIn }],
					},
				]}>
				{loading ? (
					<View style={{ paddingTop: 24 }}>
						<ActivityIndicator size="large" color={BRAND_BLUE} />
					</View>
				) : null}
				<ScrollView
					contentContainerStyle={styles.scrollContent}
					showsVerticalScrollIndicator={false}
					bounces={false}>
					<View style={styles.welcomeSection}>
						<Text style={styles.welcomeTitle}>Xin chào, {user?.email ?? 'bạn'}</Text>
						<Text style={styles.welcomeSubtitle}>
							{status?.monitoring
								? 'Hệ thống đang đọc CSI liên tục và tự động dự đoán khi đủ mẫu.'
								: 'Hệ thống đang tạm dừng. Bấm nút bắt đầu để mở giám sát liên tục.'}
						</Text>
					</View>

					{!user ? (
						<View style={styles.noticeBox}>
							<MaterialIcons name="lock" size={16} color="#B45309" />
							<Text style={styles.noticeText}>
								Bạn cần đăng nhập để điều khiển giám sát và tạo dự đoán.
							</Text>
						</View>
					) : null}

					<View style={styles.primaryCard}>
						<MaterialIcons name="search" size={120} color="#EEF3FA" style={styles.bgGlyph} />

						<View style={styles.statusRow}>
							<View style={styles.pulseDot} />
							<Text style={styles.statusLabel}>
								Trạng thái hệ thống: {status?.monitoring ? 'Đang theo dõi' : 'Tạm dừng'}
							</Text>
							<Text style={styles.liveChip}>
								{liveConnected ? 'TRỰC TIẾP' : 'NGẮT KẾT NỐI'}
							</Text>
						</View>

						<View style={styles.mainStateWrap}>
							<Text style={styles.stateCaption}>Sự hiện diện</Text>
							<View style={[styles.predictionBadge, presenceTone]}>
								<Text style={styles.predictionBadgeText}>{presenceLabel}</Text>
							</View>
							<Text style={styles.stateValue}>{displayConfidence !== null ? `${formatPercent(displayConfidence)}%` : '...'}</Text>
							{DEMO_MODE ? <Text style={styles.demoModeText}></Text> : null}
							{status?.monitoring ? <Text style={styles.autoPredictText}>Chế độ: dự đoán liên tục</Text> : null}
							{latest?.raw_presence && latest.raw_presence !== latest.presence ? (
								<Text style={styles.rawPresenceText}>Dữ liệu gốc: {latest.raw_presence}</Text>
							) : null}
							{latest?.timestamp ? (
								<Text style={styles.predictionTimeText}>
									Cập nhật: {new Date(latest.timestamp).toLocaleTimeString()}
								</Text>
							) : null}
						</View>

						{showNoEsp32DataNotice ? (
							<View style={styles.noticeBox}>
								<MaterialIcons name="sensors-off" size={16} color="#B45309" />
								<Text style={styles.noticeText}>
									Chưa có dữ liệu từ ESP32. Hãy kiểm tra kết nối và nguồn điện thiết bị.
								</Text>
							</View>
						) : null}

						{showWaitingPredictionNotice ? (
							<View style={styles.noticeBox}>
								<MaterialIcons name="hourglass-empty" size={16} color="#B45309" />
								<Text style={styles.noticeText}>
									Đã kết nối ESP32, đang chờ đủ mẫu dữ liệu để tạo dự đoán đầu tiên.
								</Text>
							</View>
						) : null}

						{livePrediction ? (
							<View style={styles.progressCard}>
								<View style={styles.progressHeaderRow}>
									<Text style={styles.progressTitle}>Tiến độ dự đoán tiếp theo</Text>
									<Text style={styles.progressPercent}>{formatPercent(livePrediction.progress_percent)}%</Text>
								</View>
								<View style={styles.progressBarOuter}>
									<View
										style={[
											styles.progressBarInner,
											{ width: formatPercentWidth(livePrediction.progress_percent) },
										]}
									/>
								</View>
								<Text style={styles.progressText}>
									Đã gom {livePrediction.buffer_size}/{livePrediction.window_size} mẫu. 
									{livePrediction.ready_for_prediction
										? ' Đã đủ cửa sổ, đang chờ dự đoán tiếp theo.'
										: ` Cần thêm ${livePrediction.samples_needed_for_first_prediction} mẫu để có dự đoán đầu tiên.`}
								</Text>
								<Text style={styles.progressDetailText}>
									Độ đầy buffer: {formatPercent(livePrediction.buffer_fill_percent)}% | 
									Tiến độ chờ prediction: {formatPercent(livePrediction.prediction_progress_percent)}%
								</Text>
								{udpStats ? (
									<Text style={styles.progressDetailText}>
										UDP đã nhận: {udpStats.received_packets} | chấp nhận: {udpStats.accepted_packets} | từ chối: {udpStats.rejected_packets}
										{udpStats.last_valid_packet_seconds_ago !== null
											? ` | hợp lệ lần cuối: ${udpStats.last_valid_packet_seconds_ago}s trước`
											: ' | chưa có gói hợp lệ'}
									</Text>
								) : null}
							</View>
						) : null}

						<View style={styles.actionRow}>
							<Pressable style={styles.primaryButton} onPress={onToggleMonitoring} disabled={!user}>
								<MaterialIcons name="bolt" size={18} color="#FFFFFF" />
								<Text style={styles.primaryButtonText}>
									{status?.monitoring ? 'Dừng dự đoán liên tục' : 'Bắt đầu dự đoán liên tục'}
								</Text>
							</Pressable>

							<Pressable onPress={() => router.push('/(tabs)/history')} style={styles.secondaryButton}>
								<Text style={styles.secondaryButtonText}>Xem lịch sử</Text>
							</Pressable>
						</View>
					</View>

					<View style={styles.metricsRow}>
						<View style={styles.metricCard}>
							<View style={styles.metricHead}>
								<MaterialIcons name="verified" size={20} color={BRAND_BLUE} />
								<Text style={styles.realTimeChip}>THỜI GIAN THỰC</Text>
							</View>
							<Text style={styles.metricLabel}>Độ tin cậy AI</Text>
							<View style={styles.metricValueRow}>
								<Text style={styles.metricValue}>{formatPercent(displayConfidence, 1, '0.0')}</Text>
								<Text style={styles.metricUnit}>%</Text>
							</View>
							{DEMO_MODE ? <Text style={styles.demoModeText}></Text> : null}
						</View>

						<View style={styles.metricCard}>
							<View style={styles.metricHead}>
								<MaterialIcons name="schedule" size={20} color="#8A95A7" />
							</View>
							<Text style={styles.metricLabel}>Cập nhật cuối</Text>
							<Text style={styles.timeText}>
								{latest ? new Date(latest.timestamp).toLocaleTimeString() : '--:--:--'}
							</Text>
							<Text style={styles.dateText}>
								{latest ? new Date(latest.timestamp).toLocaleDateString() : 'CHƯA CÓ DỮ LIỆU'}
							</Text>
						</View>
					</View>

					<View style={styles.aiCard}>
						<View style={styles.aiIconWrap}>
							<MaterialIcons name="psychology" size={26} color={BRAND_BLUE} />
						</View>

						<View style={styles.aiContent}>
								<Text style={styles.aiTitle}>Đề xuất từ AI</Text>
							<Text style={styles.aiText}>
									Phát hiện sự hiện diện của con người trong phòng theo thời gian thực. 
									Không phát hiện bất thường. Hệ thống tiếp tục giám sát sự thay đổi của 
									trạng thái phòng.
							</Text>
						</View>
					</View>

					<View style={styles.streamCard}>
						<Text style={styles.streamLabel}>LUONG DU LIEU TRUC TIEP</Text>
						<View style={styles.progressOuter}>
							<View style={styles.progressInner} />
						</View>
					</View>
				</ScrollView>
			</Animated.View>
		</SafeAreaView>
	);
}

const styles = StyleSheet.create({
	safeArea: {
		flex: 1,
		backgroundColor: '#FFFFFF',
	},
	bgGradient: {
		...StyleSheet.absoluteFillObject,
		backgroundColor: '#FFFFFF',
	},
	bgOrbTop: {
		position: 'absolute',
		width: 240,
		height: 240,
		borderRadius: 999,
		backgroundColor: '#ECF4FF',
		top: -110,
		right: -70,
	},
	bgOrbBottom: {
		position: 'absolute',
		width: 220,
		height: 220,
		borderRadius: 999,
		backgroundColor: '#F5F9FF',
		bottom: 70,
		left: -85,
	},
	header: {
		height: 64,
		paddingHorizontal: 18,
		flexDirection: 'row',
		alignItems: 'center',
		justifyContent: 'space-between',
		borderBottomWidth: 1,
		borderBottomColor: '#F1F5F9',
		backgroundColor: 'rgba(255,255,255,0.96)',
	},
	brandRow: {
		flexDirection: 'row',
		alignItems: 'center',
		gap: 8,
	},
	brandIconWrap: {
		width: 32,
		height: 32,
		borderRadius: 999,
		alignItems: 'center',
		justifyContent: 'center',
		backgroundColor: '#F8FAFC',
		borderWidth: 1,
		borderColor: '#E2E8F0',
	},
	brandText: {
		fontSize: 20,
		fontWeight: '800',
		letterSpacing: -0.7,
		color: '#0F172A',
	},
	avatar: {
		width: 38,
		height: 38,
		borderRadius: 999,
		alignItems: 'center',
		justifyContent: 'center',
		backgroundColor: '#F1F5F9',
		borderWidth: 1,
		borderColor: '#E2E8F0',
	},
	animatedArea: {
		flex: 1,
	},
	scrollContent: {
		paddingHorizontal: 18,
		paddingTop: 16,
		paddingBottom: 28,
		gap: 16,
	},
	welcomeSection: {
		gap: 6,
	},
	welcomeTitle: {
		fontSize: 34,
		fontWeight: '800',
		letterSpacing: -1,
		color: '#050A14',
	},
	welcomeSubtitle: {
		fontSize: 14,
		fontWeight: '600',
		color: BRAND_BLUE,
	},
	primaryCard: {
		borderRadius: 30,
		borderWidth: 1,
		borderColor: '#EEF2F7',
		padding: 20,
		backgroundColor: '#FFFFFF',
		overflow: 'hidden',
		gap: 16,
	},
	noticeBox: {
		flexDirection: 'row',
		alignItems: 'flex-start',
		gap: 8,
		borderWidth: 1,
		borderColor: '#FCD34D',
		backgroundColor: '#FFFBEB',
		borderRadius: 12,
		paddingHorizontal: 10,
		paddingVertical: 8,
	},
	noticeText: {
		flex: 1,
		fontSize: 12,
		fontWeight: '600',
		lineHeight: 18,
		color: '#92400E',
	},
	progressCard: {
		borderRadius: 16,
		borderWidth: 1,
		borderColor: '#DBEAFE',
		backgroundColor: '#EFF6FF',
		padding: 14,
		gap: 10,
	},
	progressHeaderRow: {
		flexDirection: 'row',
		alignItems: 'center',
		justifyContent: 'space-between',
	},
	progressTitle: {
		fontSize: 13,
		fontWeight: '800',
		color: '#0F172A',
	},
	progressPercent: {
		fontSize: 12,
		fontWeight: '800',
		color: BRAND_BLUE,
	},
	progressBarOuter: {
		height: 10,
		borderRadius: 999,
		backgroundColor: '#DBEAFE',
		overflow: 'hidden',
	},
	progressBarInner: {
		height: '100%',
		borderRadius: 999,
		backgroundColor: BRAND_BLUE,
	},
	progressText: {
		fontSize: 12,
		fontWeight: '600',
		lineHeight: 18,
		color: '#1E3A8A',
	},
	progressDetailText: {
		fontSize: 11,
		fontWeight: '600',
		lineHeight: 16,
		color: '#1D4ED8',
	},
	bgGlyph: {
		position: 'absolute',
		top: -8,
		right: -10,
	},
	statusRow: {
		flexDirection: 'row',
		alignItems: 'center',
		gap: 8,
	},
	pulseDot: {
		width: 9,
		height: 9,
		borderRadius: 999,
		backgroundColor: '#22C55E',
	},
	statusLabel: {
		fontSize: 11,
		fontWeight: '800',
		letterSpacing: 0.8,
		color: BRAND_BLUE,
		textTransform: 'uppercase',
	},
	liveChip: {
		marginLeft: 'auto',
		fontSize: 10,
		fontWeight: '800',
		color: '#16A34A',
		backgroundColor: '#DCFCE7',
		paddingHorizontal: 8,
		paddingVertical: 3,
		borderRadius: 999,
		overflow: 'hidden',
	},
	mainStateWrap: {
		gap: 4,
	},
	stateCaption: {
		color: '#94A3B8',
		fontSize: 12,
	},
	predictionBadge: {
		alignSelf: 'flex-start',
		paddingHorizontal: 12,
		paddingVertical: 6,
		borderRadius: 999,
		borderWidth: 1,
		marginTop: 4,
	},
	predictionPositive: {
		backgroundColor: '#DCFCE7',
		borderColor: '#86EFAC',
	},
	predictionNeutral: {
		backgroundColor: '#E8F1FF',
		borderColor: '#BFDBFE',
	},
	predictionBadgeText: {
		fontSize: 13,
		fontWeight: '900',
		letterSpacing: 0.8,
		color: '#0F172A',
	},
	autoPredictText: {
		marginTop: 8,
		fontSize: 12,
		fontWeight: '700',
		color: BRAND_BLUE,
		textTransform: 'uppercase',
		letterSpacing: 0.7,
	},
	stateValue: {
		color: '#0B1220',
		fontSize: 46,
		fontWeight: '800',
		letterSpacing: -1.7,
	},
	demoModeText: {
		marginTop: 6,
		fontSize: 11,
		fontWeight: '700',
		color: '#B45309',
	},
	predictionTimeText: {
		color: '#64748B',
		fontSize: 12,
		fontWeight: '600',
		marginTop: 2,
	},
	rawPresenceText: {
		color: '#64748B',
		fontSize: 12,
		fontWeight: '700',
		marginTop: 4,
	},
	actionRow: {
		flexDirection: 'row',
		gap: 10,
		flexWrap: 'wrap',
	},
	primaryButton: {
		backgroundColor: '#09090B',
		borderRadius: 16,
		paddingHorizontal: 18,
		paddingVertical: 13,
		flexDirection: 'row',
		alignItems: 'center',
		gap: 8,
	},
	primaryButtonText: {
		color: '#FFFFFF',
		fontSize: 14,
		fontWeight: '700',
	},
	secondaryButton: {
		backgroundColor: '#F1F5F9',
		borderRadius: 16,
		paddingHorizontal: 18,
		paddingVertical: 13,
		flexDirection: 'row',
		alignItems: 'center',
		justifyContent: 'center',
		gap: 8,
	},
	secondaryButtonDisabled: {
		opacity: 0.7,
	},
	secondaryButtonTextDisabled: {
		color: '#94A3B8',
		alignItems: 'center',
		justifyContent: 'center',
	},
	secondaryButtonText: {
		color: '#0F172A',
		fontSize: 14,
		fontWeight: '700',
	},
	metricsRow: {
		gap: 12,
	},
	metricCard: {
		borderRadius: 30,
		borderWidth: 1,
		borderColor: '#EEF2F7',
		backgroundColor: '#FFFFFF',
		padding: 20,
		gap: 6,
	},
	metricHead: {
		flexDirection: 'row',
		justifyContent: 'space-between',
		alignItems: 'center',
		marginBottom: 4,
	},
	realTimeChip: {
		fontSize: 10,
		color: BRAND_BLUE,
		backgroundColor: '#E8F1FF',
		fontWeight: '700',
		paddingHorizontal: 8,
		paddingVertical: 3,
		borderRadius: 999,
		overflow: 'hidden',
	},
	metricLabel: {
		color: '#94A3B8',
		fontSize: 13,
	},
	metricValueRow: {
		flexDirection: 'row',
		alignItems: 'flex-end',
		gap: 2,
	},
	metricValue: {
		fontSize: 46,
		lineHeight: 52,
		fontWeight: '800',
		letterSpacing: -1,
		color: '#0B1220',
	},
	metricUnit: {
		fontSize: 22,
		fontWeight: '700',
		color: BRAND_BLUE,
		marginBottom: 7,
	},
	timeText: {
		fontSize: 34,
		fontWeight: '700',
		color: '#0B1220',
		letterSpacing: -0.5,
	},
	dateText: {
		color: BRAND_BLUE,
		fontWeight: '800',
		fontSize: 11,
		letterSpacing: 0.6,
	},
	aiCard: {
		borderRadius: 30,
		borderWidth: 1,
		borderColor: '#EEF2F7',
		backgroundColor: '#FFFFFF',
		padding: 18,
		flexDirection: 'row',
		gap: 12,
	},
	aiIconWrap: {
		width: 54,
		height: 54,
		borderRadius: 999,
		backgroundColor: '#F8FAFC',
		borderWidth: 1,
		borderColor: '#E2E8F0',
		alignItems: 'center',
		justifyContent: 'center',
	},
	aiContent: {
		flex: 1,
		gap: 5,
	},
	aiTitle: {
		color: '#0B1220',
		fontWeight: '800',
		fontSize: 18,
	},
	aiText: {
		color: '#64748B',
		lineHeight: 21,
		fontSize: 13,
	},
	streamCard: {
		borderRadius: 30,
		borderWidth: 1,
		borderColor: '#EEF2F7',
		backgroundColor: '#FFFFFF',
		padding: 20,
		minHeight: 120,
		justifyContent: 'center',
		gap: 14,
	},
	streamLabel: {
		color: BRAND_BLUE,
		fontWeight: '800',
		fontSize: 11,
		letterSpacing: 1.1,
		textAlign: 'center',
	},
	progressOuter: {
		width: '100%',
		height: 14,
		borderRadius: 999,
		borderWidth: 1,
		borderColor: '#E2E8F0',
		backgroundColor: '#F8FAFC',
		padding: 1,
	},
	progressInner: {
		width: '67%',
		height: '100%',
		borderRadius: 999,
		backgroundColor: '#0B0F16',
	},
});
