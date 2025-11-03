import 'package:flutter/material.dart';
import 'package:sparky_client/app_colors.dart';

/// TEST SCREEN - Minimal color test to verify colors work
/// This bypasses ALL theme system and uses ONLY explicit colors
class TestColorScreen extends StatelessWidget {
  const TestColorScreen({super.key});

  @override
  Widget build(BuildContext context) {
    // Use centralized color constants
    debugPrint('🔍 COLOR DEBUG - Using AppColors:');
    debugPrint('  Powder Blue: R=${AppColors.powderBlue.red}, G=${AppColors.powderBlue.green}, B=${AppColors.powderBlue.blue}');
    debugPrint('  Thistle: R=${AppColors.thistle.red}, G=${AppColors.thistle.green}, B=${AppColors.thistle.blue}');
    debugPrint('  Pale Green: R=${AppColors.paleGreen.red}, G=${AppColors.paleGreen.green}, B=${AppColors.paleGreen.blue}');
    
    return Material(
      // NO THEME - Just raw Material with explicit colors
      child: ColoredBox(
        color: AppColors.powderBlue, // Powder Blue
        child: Column(
          children: [
            // Test AppBar
            ColoredBox(
              color: AppColors.thistle, // Thistle
              child: SizedBox(
                height: 56,
                width: double.infinity,
                child: Center(
                  child: Text(
                    'THISTLE APPBAR - Should be #D8BFD8',
                    style: TextStyle(
                      color: Colors.black,
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
            ),
            // Test Center Content
            Expanded(
              child: Center(
                child: ColoredBox(
                  color: AppColors.paleGreen, // Pale Green
                  child: Padding(
                    padding: const EdgeInsets.all(40.0),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          'PALE GREEN BOX',
                          style: TextStyle(
                            color: Colors.black,
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 20),
                        Text(
                          'Should be #98FB98',
                          style: TextStyle(
                            color: Colors.black,
                            fontSize: 16,
                          ),
                        ),
                        const SizedBox(height: 40),
                        Text(
                          'Background should be Powder Blue #B0E0E6',
                          style: TextStyle(
                            color: Colors.black,
                            fontSize: 14,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
            // Color verification boxes - Try darker/more saturated versions
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                children: [
                  Text(
                    'EXACT HEX VALUES (as specified):',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      _ColorBox(Color(0xFFB0E0E6), 'Powder Blue'),
                      _ColorBox(Color(0xFFD8BFD8), 'Thistle'),
                      _ColorBox(Color(0xFF98FB98), 'Pale Green'),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'ALTERNATIVE DARKER VERSIONS (for comparison):',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      _ColorBox(Color(0xFF87CEEB), 'Sky Blue (darker)'),
                      _ColorBox(Color(0xFFC8A2C8), 'Lilac (darker)'),
                      _ColorBox(Color(0xFF90EE90), 'Light Green (darker)'),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ColorBox extends StatelessWidget {
  final Color color;
  final String label;

  const _ColorBox(this.color, this.label);

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          width: 100,
          height: 100,
          color: color,
          child: Center(
            child: Text(
              color.value.toRadixString(16).substring(2).toUpperCase(),
              style: TextStyle(
                color: Colors.black,
                fontSize: 12,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ),
        const SizedBox(height: 8),
        Text(
          label,
          style: TextStyle(fontSize: 12),
        ),
      ],
    );
  }
}
