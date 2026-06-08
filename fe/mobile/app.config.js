module.exports = ({ config }) => {
  const apiBaseUrl = process.env.EXPO_PUBLIC_API_BASE_URL?.trim();

  return {
    ...config,
    extra: {
      ...(config.extra ?? {}),
      ...(apiBaseUrl ? { apiBaseUrl } : {}),
    },
  };
};