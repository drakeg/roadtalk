const { AndroidConfig } = require("expo/config-plugins");

module.exports = function withRoadTalkAudioOnlyWebRTC(config) {
  config.ios = { ...config.ios, bitcode: false };
  return AndroidConfig.Permissions.withPermissions(config, [
    "android.permission.ACCESS_NETWORK_STATE",
    "android.permission.BLUETOOTH",
    "android.permission.INTERNET",
    "android.permission.MODIFY_AUDIO_SETTINGS",
    "android.permission.RECORD_AUDIO",
  ]);
};
