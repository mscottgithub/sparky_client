import 'package:flutter/material.dart';

/// Application Color Constants
/// Updated with darker colors as specified by user
class AppColors {
  // Powder Blue (darker version) #8BBCC2
  // R: 139, G: 188, B: 194
  static const Color powderBlue = Color(0xFF8BBCC2);
  
  // Thistle (darker/more muted) #977597
  // R: 151, G: 117, B: 151
  static const Color thistle = Color(0xFF977597);
  
  // Pale Green #78C778
  // R: 120, G: 199, B: 120
  static const Color paleGreen = Color(0xFF78C778);
  
  // Alternative RGB methods if needed
  static Color get powderBlueRGB => Color.fromRGBO(139, 188, 194, 1.0);
  static Color get thistleRGB => Color.fromRGBO(151, 117, 151, 1.0);
  static Color get paleGreenRGB => Color.fromRGBO(120, 199, 120, 1.0);
}