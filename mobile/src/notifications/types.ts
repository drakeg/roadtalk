export type NotificationClass = "account" | "channel_activity" | "urgent_alert";
export type NotificationPriority = "normal" | "high" | "urgent";
export type NotificationSource =
  | "roadtalk_account"
  | "roadtalk_channel"
  | "user_generated_urgent";
export type NotificationState = "read" | "dismissed";

export type NotificationPreferences = {
  channelActivityEnabled: boolean;
  urgentAlertEnabled: boolean;
  version: number;
};

export type NotificationRecord = {
  id: string;
  notificationClass: NotificationClass;
  priority: NotificationPriority;
  source: NotificationSource;
  title: string | null;
  message: string;
  channelLabel: string | null;
  issuedAt: string;
  expiresAt: string;
  readAt: string | null;
  dismissedAt: string | null;
  version: number;
  verified: false | null;
  emergencyService: false | null;
  deliveryGuaranteed: false | null;
  safetyNotEmergencyService: "RoadTalk is not an emergency service." | null;
  safetyDeliveryNotGuaranteed: "Delivery is not guaranteed." | null;
  safetyEmergencyServicesGuidance:
    | "Contact local emergency services directly when emergency assistance is needed."
    | null;
  safetyUnverified: "This alert is user-generated and unverified." | null;
};

export type NotificationInbox = {
  items: NotificationRecord[];
};

export type UrgentAlertReceipt = {
  accepted: true;
  recipientCount: number;
  issuedAt: string;
  expiresAt: string;
};
