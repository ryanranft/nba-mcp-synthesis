# MCP Tool Registry

**Purpose**: Searchable registry of all 90+ MCP tools
**Last Updated**: 2025-10-11
**Total Tools**: 90 registered + 3 implemented + 16 pending = 109 total

---

## 🔍 Quick Search

### By Category
- **Database Tools**: 15 tools
- **S3 Tools**: 10 tools
- **File Tools**: 8 tools
- **Action Tools**: 12 tools
- **Book Tools**: 10 tools
- **Math Tools**: 7 tools
- **Stats Tools**: 15 tools
- **NBA Tools**: 13 tools
- **ML Tools**: 33 tools
- **AWS Tools**: 10 tools

### By Status
- **Registered**: 90 tools ✅
- **Implemented**: 3 tools (not registered)
- **Pending**: 16 tools

---

## 📊 Database Tools (15 tools)

### Core Database Operations
- **query_database** - Execute SQL SELECT queries
- **list_tables** - List all database tables
- **get_table_schema** - Get table structure and schema
- **get_table_info** - Get table metadata and statistics
- **count_rows** - Count rows in tables

### Data Manipulation
- **create_table** - Create new database tables
- **insert_data** - Insert records into tables
- **update_data** - Update existing records
- **delete_data** - Delete records from tables
- **drop_table** - Drop database tables

### Advanced Operations
- **execute_raw_sql** - Execute arbitrary SQL commands
- **bulk_insert** - Bulk data insertion operations
- **transaction_execute** - Transaction support
- **backup_database** - Database backup operations
- **restore_database** - Database restore operations

---

## ☁️ S3 Tools (10 tools)

### File Operations
- **list_s3_files** - List S3 objects and files
- **get_s3_file** - Download files from S3
- **upload_s3_file** - Upload files to S3
- **delete_s3_file** - Delete S3 objects
- **copy_s3_file** - Copy S3 objects

### Bucket Management
- **create_s3_bucket** - Create S3 buckets
- **delete_s3_bucket** - Delete S3 buckets
- **list_s3_buckets** - List all S3 buckets
- **get_s3_metadata** - Get S3 object metadata
- **set_s3_permissions** - Manage S3 permissions

---

## 📁 File Tools (8 tools)

### File Operations
- **read_file** - Read local files
- **write_file** - Write local files
- **append_file** - Append to existing files
- **delete_file** - Delete local files
- **copy_file** - Copy files

### File Management
- **list_files** - List directory contents
- **search_files** - Search file contents
- **get_file_metadata** - Get file metadata

---

## 🎯 Action Tools (12 tools)

### Player Analytics
- **analyze_player_performance** - Player performance analysis
- **compare_players** - Player comparison
- **get_advanced_metrics** - Advanced player metrics
- **analyze_shooting_efficiency** - Shooting analysis
- **evaluate_defensive_impact** - Defense metrics
- **calculate_win_shares** - Win shares calculation

### Team Analytics
- **get_team_statistics** - Team statistics
- **predict_game_outcome** - Game predictions
- **generate_trade_analysis** - Trade impact analysis
- **predict_playoff_probability** - Playoff odds

### Advanced Analytics
- **analyze_game_flow** - Game flow analysis
- **evaluate_coaching_impact** - Coaching metrics

---

## 📚 Book Tools (10 tools)

### EPUB Operations
- **read_epub_book** - Read EPUB books
- **extract_epub_text** - Extract text from EPUB
- **get_epub_metadata** - Get EPUB metadata
- **search_epub_content** - Search EPUB content
- **convert_epub_to_text** - Convert EPUB to text

### PDF Operations
- **read_pdf_book** - Read PDF books
- **extract_pdf_text** - Extract text from PDF
- **get_pdf_metadata** - Get PDF metadata
- **search_pdf_content** - Search PDF content
- **convert_pdf_to_text** - Convert PDF to text

---

## 🔢 Math Tools (7 tools)

### Basic Math
- **add_numbers** - Addition operations
- **subtract_numbers** - Subtraction operations
- **multiply_numbers** - Multiplication operations
- **divide_numbers** - Division operations

### Advanced Math
- **calculate_percentage** - Percentage calculations
- **calculate_average** - Average calculations
- **calculate_statistics** - Statistical calculations

---

## 📈 Stats Tools (15 tools)

### Descriptive Statistics
- **calculate_mean** - Mean calculation
- **calculate_median** - Median calculation
- **calculate_mode** - Mode calculation
- **calculate_standard_deviation** - Standard deviation
- **calculate_variance** - Variance calculation

### Correlation & Regression
- **calculate_correlation** - Correlation analysis
- **linear_regression** - Linear regression
- **multiple_regression** - Multiple regression
- **logistic_regression** - Logistic regression

### Statistical Tests
- **t_test** - T-test analysis
- **chi_square_test** - Chi-square test
- **anova_test** - ANOVA test
- **mann_whitney_test** - Mann-Whitney test

### Advanced Statistics
- **confidence_interval** - Confidence intervals
- **hypothesis_testing** - Hypothesis testing
- **statistical_significance** - Significance testing

---

## 🏀 NBA Tools (13 tools)

### Player Metrics
- **nba_player_efficiency_rating** - Player Efficiency Rating (PER)
- **nba_true_shooting_percentage** - True Shooting Percentage
- **nba_usage_rate** - Usage Rate
- **nba_win_shares** - Win Shares (NEW - Oct 11, 2025)
- **nba_box_plus_minus** - Box Plus/Minus (NEW - Oct 11, 2025)

### Team Metrics
- **nba_team_efficiency** - Team efficiency metrics
- **nba_offensive_rating** - Offensive rating
- **nba_defensive_rating** - Defensive rating
- **nba_net_rating** - Net rating

### Game Metrics
- **nba_pace** - Pace calculation
- **nba_possessions** - Possession calculation
- **nba_four_factors** - Four factors analysis
- **nba_clutch_stats** - Clutch statistics

---

## 🤖 ML Tools (33 tools)

### Clustering (6 tools)
- **k_means_clustering** - K-means clustering
- **hierarchical_clustering** - Hierarchical clustering
- **dbscan_clustering** - DBSCAN clustering
- **calculate_euclidean_distance** - Euclidean distance
- **calculate_manhattan_distance** - Manhattan distance
- **calculate_cosine_similarity** - Cosine similarity

### Classification (6 tools)
- **logistic_regression** - Logistic regression
- **decision_tree_classifier** - Decision tree
- **random_forest_classifier** - Random forest
- **svm_classifier** - Support Vector Machine
- **naive_bayes_classifier** - Naive Bayes
- **gradient_boosting_classifier** - Gradient boosting

### Anomaly Detection (6 tools)
- **detect_outliers_zscore** - Z-score outlier detection
- **detect_outliers_iqr** - IQR outlier detection
- **detect_outliers_isolation_forest** - Isolation forest
- **detect_outliers_one_class_svm** - One-class SVM
- **detect_outliers_local_outlier_factor** - Local outlier factor
- **detect_outliers_elliptic_envelope** - Elliptic envelope

### Feature Engineering (6 tools)
- **normalize_features** - Feature normalization
- **standardize_features** - Feature standardization
- **scale_features** - Feature scaling
- **select_features** - Feature selection
- **create_polynomial_features** - Polynomial features
- **reduce_dimensionality** - Dimensionality reduction

### Model Evaluation (6 tools)
- **calculate_accuracy** - Accuracy calculation
- **calculate_precision** - Precision calculation
- **calculate_recall** - Recall calculation
- **calculate_f1_score** - F1 score calculation
- **calculate_roc_auc** - ROC AUC calculation
- **calculate_confusion_matrix** - Confusion matrix

### Model Validation (3 tools)
- **k_fold_split** - K-fold cross-validation
- **train_test_split** - Train-test split
- **cross_validate_model** - Cross-validation

---

## ☁️ AWS Tools (10 tools)

### Glue Tools (2 tools)
- **get_glue_table_metadata** - Get Glue table metadata
- **list_glue_tables** - List Glue tables

### Lambda Tools (3 tools)
- **invoke_lambda_function** - Invoke Lambda functions
- **list_lambda_functions** - List Lambda functions
- **get_lambda_function_info** - Get Lambda function info

### CloudWatch Tools (3 tools)
- **get_cloudwatch_metrics** - Get CloudWatch metrics
- **list_cloudwatch_logs** - List CloudWatch logs
- **create_cloudwatch_alarm** - Create CloudWatch alarms

### Other AWS Tools (2 tools)
- **get_aws_account_info** - Get AWS account info
- **list_aws_resources** - List AWS resources

---

## 🔍 Tool Search

### Quick Find by Name
```bash
# Find tool by name
grep -r "tool_name" mcp_server/tools/

# Find tools by category
find mcp_server/tools/ -name "*database*" -o -name "*s3*"

# Search tool descriptions
grep -r "description" mcp_server/tools/
```

### By Implementation Status
- **Registered**: 90 tools (in fastmcp_server.py)
- **Implemented**: 3 tools (not yet registered)
- **Pending**: 16 tools (planned)

---

## 📊 Tool Statistics

### Registration Status
- **Sprint 5**: 33 tools ✅
- **Sprint 6**: 22 tools ✅
- **Sprint 7**: 20 tools ✅
- **Sprint 8**: 15 tools ✅
- **Total Registered**: 90 tools

### Tool Categories
- **Infrastructure**: 33 tools (Database, S3, File)
- **Analytics**: 40 tools (Action, Stats, NBA)
- **ML/AI**: 33 tools (Clustering, Classification, etc.)
- **Integration**: 3 tools (Book, Math, AWS)

---

## 🎯 Context Optimization

**Purpose**: Tool registry provides focused tool information without loading implementation details

**Navigation Strategy**:
- Use this registry to find specific tools
- Reference tool categories for related functionality
- Avoid loading multiple tool files simultaneously

**Token Usage**:
- This registry: ~100 tokens
- Individual tool file: 200-500 tokens
- Total for tool lookup: 300-600 tokens

---

## 📈 Tool Usage Patterns

### Most Used Tools
1. **query_database** - Database queries
2. **list_tables** - Table discovery
3. **get_table_schema** - Schema information
4. **analyze_player_performance** - Player analytics
5. **calculate_statistics** - Statistical calculations

### Tool Categories by Usage
- **Database Tools**: High usage (core functionality)
- **Analytics Tools**: Medium usage (analysis tasks)
- **ML Tools**: Medium usage (advanced analytics)
- **File Tools**: Low usage (utility functions)

---

**Note**: This registry is part of Phase 6 of the Context Optimization plan. Tool information is organized to provide focused tool discovery with minimal implementation context usage.
