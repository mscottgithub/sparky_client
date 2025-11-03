import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sparky_client/services/config_service.dart';

/// Configuration service provider
/// Provides global configuration settings
final configProvider = Provider<ConfigService>((ref) {
  return ConfigService();
});

