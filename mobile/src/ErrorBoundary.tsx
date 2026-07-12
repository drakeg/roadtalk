import type { ErrorInfo, ReactNode } from "react";
import { Component } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, spacing } from "./theme";

type Props = { children: ReactNode };
type State = { hasError: boolean };

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    if (__DEV__) {
      console.error("mobile.render.failure", error.name, info.componentStack);
    }
  }

  private retry = (): void => {
    this.setState({ hasError: false });
  };

  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }

    return (
      <View accessibilityRole="alert" style={styles.container}>
        <Text accessibilityRole="header" style={styles.title}>
          RoadTalk could not start
        </Text>
        <Text style={styles.body}>
          No personal data was sent. Try loading the application again.
        </Text>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Try loading RoadTalk again"
          onPress={this.retry}
          style={styles.button}
        >
          <Text style={styles.buttonText}>Try again</Text>
        </Pressable>
      </View>
    );
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    justifyContent: "center",
    padding: spacing.xlarge,
    gap: spacing.medium,
  },
  title: {
    color: colors.danger,
    fontSize: 28,
    fontWeight: "700",
  },
  body: {
    color: colors.text,
    fontSize: 17,
    lineHeight: 25,
  },
  button: {
    alignItems: "center",
    backgroundColor: colors.primary,
    borderRadius: 12,
    minHeight: 48,
    justifyContent: "center",
  },
  buttonText: {
    color: colors.surface,
    fontSize: 17,
    fontWeight: "600",
  },
});
