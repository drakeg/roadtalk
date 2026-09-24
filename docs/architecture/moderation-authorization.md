# Moderation authorization composition

Sprint 12 mute/block enforcement is a server-side denial layer applied after RoadTalk's existing account/session, current-location/consent, proximity/Same-road, channel, convoy and receive-grant eligibility.

The moderation filter accepts only the already-authorized receiver tuple and can return that tuple or a subset. It cannot construct, restore or add a recipient.

## Directional behavior

- If a receiver actively mutes the sender, that receiver is removed from the sender's delivery audience.
- If a receiver actively blocks the sender, that receiver is removed.
- If the sender actively blocks a receiver, that receiver is removed.
- A sender muting a receiver affects what the sender receives from that account; it does not suppress the receiver from hearing the sender.
- Revoked, expired or time-expired restrictions do not deny delivery.

Active restriction state is persisted as account IDs, kind, state, optional expiry, terminal timestamp, version and normal row timestamps only. No channel, convoy, location, media/provider grant or client assertion can bypass an active applicable restriction.

D04 does not add public restriction-management APIs or UI; those surfaces remain later Sprint 12 deliverables.
