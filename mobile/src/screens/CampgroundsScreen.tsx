import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import type { RootStackParamList } from "../AppNavigator";
import {
  filterCampgrounds,
  loadCampgroundCatalog,
  loadCurrentCampgroundContext,
  type CampgroundRecord,
} from "../campgrounds/api";
import { useSessionClient } from "../session/SessionContext";
import { colors, spacing } from "../theme";

type Props = NativeStackScreenProps<RootStackParamList, "Campgrounds">;

export function CampgroundsScreen({ navigation }: Props) {
  const session = useSessionClient();
  const [rows, setRows] = useState<CampgroundRecord[]>([]);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("Loading deterministic test campground catalog…");
  const [context, setContext] = useState("Current campground context unavailable.");
  const [loading, setLoading] = useState(true);

  async function refresh(): Promise<void> {
    setLoading(true);
    try {
      const catalog = await loadCampgroundCatalog();
      setRows(catalog.campgrounds);
      setStatus(`${catalog.campgrounds.length} deterministic test campground(s) available. Not a live directory.`);
    } catch {
      setRows([]);
      setStatus("Campground test catalog is unavailable. No stale or inferred campground data is shown.");
    }
    try {
      const current = await loadCurrentCampgroundContext(session);
      setContext(
        current.state === "current" && current.context !== null
          ? `Current server-derived context: ${current.context.name}. This does not grant communication access.`
          : "No current campground context. Permission-denied, stale, missing, or unmatched location states fail closed.",
      );
    } catch {
      setContext("Current campground context unavailable. RoadTalk will not infer or retain a visit from this failure.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  const filtered = useMemo(() => filterCampgrounds(rows, query, "", ""), [rows, query]);

  return (
    <View style={styles.container}>
      <Text accessibilityRole="header" style={styles.title}>Campgrounds</Text>
      <Text style={styles.notice}>
        Deterministic test data only. No reservations, payments, campsite occupancy, member lists, or background location/audio.
      </Text>
      <View accessibilityLiveRegion="polite" style={styles.panel}>
        <Text style={styles.panelTitle}>Current campground context</Text>
        <Text style={styles.body}>{context}</Text>
      </View>
      <TextInput
        accessibilityLabel="Search campgrounds"
        onChangeText={setQuery}
        placeholder="Search name or locality"
        placeholderTextColor={colors.muted}
        style={styles.input}
        value={query}
      />
      <View accessibilityLiveRegion="polite">
        <Text style={styles.status}>{status}</Text>
      </View>
      {loading ? <ActivityIndicator accessibilityLabel="Loading campgrounds" /> : null}
      <FlatList
        data={filtered}
        keyExtractor={(item) => item.campground_id}
        ListEmptyComponent={<Text style={styles.body}>No campground records match this search.</Text>}
        renderItem={({ item }) => (
          <View style={styles.card} accessible accessibilityLabel={`${item.name}, ${item.locality}, ${item.region}`}>
            <Text style={styles.cardTitle}>{item.name}</Text>
            <Text style={styles.body}>{item.locality}, {item.region} · {item.category.replaceAll("_", " ")}</Text>
            <Text style={styles.meta}>Deterministic test data · campground centroid metadata · not live availability</Text>
          </View>
        )}
      />
      <View style={styles.actions}>
        <Pressable accessibilityRole="button" accessibilityLabel="Refresh campground data" onPress={() => void refresh()} style={styles.button}>
          <Text style={styles.buttonText}>Refresh</Text>
        </Pressable>
        <Pressable accessibilityRole="button" accessibilityLabel="Open existing channel controls" onPress={() => navigation.navigate("Channels")} style={styles.secondaryButton}>
          <Text style={styles.secondaryText}>Open channel controls</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, padding: spacing.large, gap: spacing.medium },
  title: { color: colors.text, fontSize: 30, fontWeight: "700" },
  notice: { color: colors.muted, fontSize: 15, lineHeight: 22 },
  panel: { backgroundColor: colors.surface, borderColor: colors.border, borderWidth: 1, borderRadius: 12, padding: spacing.medium, gap: spacing.small },
  panelTitle: { color: colors.text, fontSize: 18, fontWeight: "600" },
  body: { color: colors.text, fontSize: 16, lineHeight: 23 },
  input: { minHeight: 48, borderColor: colors.border, borderWidth: 1, borderRadius: 10, color: colors.text, paddingHorizontal: spacing.medium, backgroundColor: colors.surface },
  status: { color: colors.muted, fontSize: 14 },
  card: { backgroundColor: colors.surface, borderColor: colors.border, borderWidth: 1, borderRadius: 12, padding: spacing.medium, marginBottom: spacing.medium, gap: spacing.small },
  cardTitle: { color: colors.text, fontSize: 18, fontWeight: "600" },
  meta: { color: colors.muted, fontSize: 13, lineHeight: 19 },
  actions: { gap: spacing.small },
  button: { minHeight: 48, borderRadius: 12, alignItems: "center", justifyContent: "center", backgroundColor: colors.primary },
  buttonText: { color: colors.surface, fontSize: 16, fontWeight: "600" },
  secondaryButton: { minHeight: 48, borderRadius: 12, alignItems: "center", justifyContent: "center", borderColor: colors.primary, borderWidth: 2 },
  secondaryText: { color: colors.primary, fontSize: 16, fontWeight: "600" },
});
