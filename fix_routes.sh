#!/bin/zsh
# --- Fix wrong url_for references in templates ---

sed -i '' "s/url_for('compatibility')/url_for('compatibility_page')/g" templates/*.html
sed -i '' "s/url_for('medication_administration_route')/url_for('medication_administration')/g" templates/*.html
sed -i '' "s/url_for('small_dose_route')/url_for('fentanyl_small_dose_route')/g" templates/*.html
sed -i '' "s/url_for('fluids')/url_for('fluids_route')/g" templates/*.html
sed -i '' "s/url_for('home')/url_for('index')/g" templates/*.html
