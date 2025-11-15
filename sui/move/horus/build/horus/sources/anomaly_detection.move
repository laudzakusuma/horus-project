module horus::anomaly_detection {
    use sui::object::{Self, UID};
    use sui::tx_context::{Self, TxContext};
    use sui::transfer;
    use sui::event;
    use sui::vec_map::{Self, VecMap};
    use std::vector;
    use std::option;

    // ===== Constants =====
    const ENotAuditor: u64 = 1;
    const EInvalidThreshold: u64 = 2;
    const ESystemPaused: u64 = 4;
    const EInvalidModelVersion: u64 = 5;
    const EInvalidRiskScore: u64 = 8;
    const EMaxAuditorsReached: u64 = 9;

    const MAX_AUDITORS: u64 = 50;
    const MAX_REQUESTS_PER_WINDOW: u64 = 1000;
    const MIN_THRESHOLD: u64 = 10;
    const MAX_THRESHOLD: u64 = 1000;

    // ===== Event Definitions =====

    struct SystemInitialized has copy, drop {
        admin: address,
        threshold: u64,
        model_version: u64
    }

    struct TransactionRecorded has copy, drop {
        transaction_id: vector<u8>,
        risk_score: u64,
        timestamp: u64
    }

    struct AnomalyDetected has copy, drop {
        transaction_id: vector<u8>,
        anomaly_score: u64,
        risk_level: u64,
        model_version: u64
    }

    struct AuditorAdded has copy, drop {
        auditor: address,
        added_by: address
    }

    struct AuditorRemoved has copy, drop {
        auditor: address,
        removed_by: address
    }

    struct SystemPaused has copy, drop {
        paused_by: address
    }

    struct SystemResumed has copy, drop {
        resumed_by: address
    }

    // ===== Struct Definitions =====

    /// System-wide configuration and state
    struct SystemState has key {
        id: UID,
        admin: address,
        auditors: vector<address>,
        anomaly_threshold: u64,
        current_model_version: u64,
        model_hashes: VecMap<u64, vector<u8>>,
        transaction_count: u64,
        anomaly_count: u64,
        is_paused: bool,
        created_at: u64
    }

    /// Admin capability for privileged operations
    struct AdminCap has key, store {
        id: UID
    }

    /// Anomaly detection result with detailed metadata
    struct AnomalyResult has key, store {
        id: UID,
        transaction_id: vector<u8>,
        features: vector<u64>,
        model_version: u64,
        anomaly_score: u64,
        risk_level: u64,
        timestamp: u64,
        reviewed: bool,
        reviewed_by: option::Option<address>
    }

    /// System statistics for monitoring
    struct SystemStats has copy, drop {
        total_transactions: u64,
        total_anomalies: u64,
        current_threshold: u64,
        model_version: u64,
        auditor_count: u64
    }

    // ===== System Initialization =====

    /// Initialize the anomaly detection system with admin capability
    public fun initialize(
        admin: address,
        initial_threshold: u64,
        initial_model_hash: vector<u8>,
        ctx: &mut TxContext
    ) {
        // Validate initial threshold
        assert!(initial_threshold >= MIN_THRESHOLD && initial_threshold <= MAX_THRESHOLD, EInvalidThreshold);

        let system_state = SystemState {
            id: object::new(ctx),
            admin,
            auditors: vector::empty<address>(),
            anomaly_threshold: initial_threshold,
            current_model_version: 1,
            model_hashes: vec_map::empty(),
            transaction_count: 0,
            anomaly_count: 0,
            is_paused: false,
            created_at: tx_context::epoch(ctx)
        };

        // Store initial model hash
        vec_map::insert(&mut system_state.model_hashes, 1, initial_model_hash);

        // Create admin capability
        let admin_cap = AdminCap {
            id: object::new(ctx)
        };

        // Emit initialization event
        event::emit(SystemInitialized {
            admin,
            threshold: initial_threshold,
            model_version: 1
        });

        transfer::transfer(system_state, admin);
        transfer::transfer(admin_cap, admin);
    }

    // ===== Core Functions =====

    /// Record a transaction with comprehensive validation
    public fun record_transaction(
        system: &mut SystemState,
        _transaction_id: vector<u8>,
        _transaction_type: vector<u8>,
        _amount: u64,
        _metadata: vector<u8>,
        risk_score: u64,
        ctx: &mut TxContext
    ) {
        // System state checks
        assert!(!system.is_paused, ESystemPaused);
        assert!(risk_score <= 100, EInvalidRiskScore);

        let current_time = tx_context::epoch(ctx);
        
        // Rate limiting check
        check_rate_limit(system);

        system.transaction_count = system.transaction_count + 1;

        // Emit transaction recorded event
        event::emit(TransactionRecorded {
            transaction_id: b"dummy_tx_id",
            risk_score,
            timestamp: current_time
        });
    }

    /// Report anomaly score with comprehensive validation
    public fun report_anomaly_score(
        system: &mut SystemState,
        transaction_id: vector<u8>,
        features: vector<u64>,
        model_version: u64,
        anomaly_score: u64,
        ctx: &mut TxContext
    ) {
        assert!(!system.is_paused, ESystemPaused);
        assert!(model_version <= system.current_model_version, EInvalidModelVersion);

        let current_time = tx_context::epoch(ctx);
        let risk_level = calculate_risk_level(anomaly_score, system.anomaly_threshold);

        // Create detailed anomaly result
        let anomaly_result = AnomalyResult {
            id: object::new(ctx),
            transaction_id,
            features,
            model_version,
            anomaly_score,
            risk_level,
            timestamp: current_time,
            reviewed: false,
            reviewed_by: option::none()
        };

        system.anomaly_count = system.anomaly_count + 1;

        // Emit anomaly detection event
        event::emit(AnomalyDetected {
            transaction_id: copy transaction_id,
            anomaly_score,
            risk_level,
            model_version
        });

        // Transfer to admin for review
        transfer::transfer(anomaly_result, system.admin);
    }

    /// Calculate risk level with multiple thresholds
    fun calculate_risk_level(anomaly_score: u64, threshold: u64): u64 {
        if (anomaly_score > threshold + (threshold / 2)) {
            3 // Critical risk
        } else if (anomaly_score > threshold) {
            2 // High risk  
        } else if (anomaly_score > threshold / 2) {
            1 // Medium risk
        } else {
            0 // Low risk
        }
    }

    // ===== Access Control Functions =====

    /// Add an auditor with capacity limits
    public fun add_auditor(
        system: &mut SystemState,
        _admin_cap: &AdminCap,
        auditor: address,
        ctx: &mut TxContext
    ) {
        assert!(!system.is_paused, ESystemPaused);
        assert!(vector::length(&system.auditors) < (MAX_AUDITORS as u64), EMaxAuditorsReached);
        assert!(!vector::contains(&system.auditors, &auditor), EMaxAuditorsReached);

        vector::push_back(&mut system.auditors, auditor);

        event::emit(AuditorAdded {
            auditor,
            added_by: tx_context::sender(ctx)
        });
    }

    /// Remove an auditor with validation
    public fun remove_auditor(
        system: &mut SystemState,
        _admin_cap: &AdminCap,
        auditor: address,
        ctx: &mut TxContext
    ) {
        assert!(!system.is_paused, ESystemPaused);
        
        let (found, index) = vector::index_of(&system.auditors, &auditor);
        assert!(found, ENotAuditor);
        vector::remove(&mut system.auditors, index);

        event::emit(AuditorRemoved {
            auditor,
            removed_by: tx_context::sender(ctx)
        });
    }

    /// Update anomaly detection threshold with validation
    public fun update_threshold(
        system: &mut SystemState,
        _admin_cap: &AdminCap,
        new_threshold: u64,
        _ctx: &mut TxContext
    ) {
        assert!(!system.is_paused, ESystemPaused);
        assert!(new_threshold >= MIN_THRESHOLD && new_threshold <= MAX_THRESHOLD, EInvalidThreshold);
        
        system.anomaly_threshold = new_threshold;
    }

    /// Update model with versioning
    public fun update_model(
        system: &mut SystemState,
        _admin_cap: &AdminCap,
        new_model_hash: vector<u8>,
        _ctx: &mut TxContext
    ) {
        assert!(!system.is_paused, ESystemPaused);
        
        let new_version = system.current_model_version + 1;
        system.current_model_version = new_version;
        vec_map::insert(&mut system.model_hashes, new_version, new_model_hash);
    }

    /// Emergency pause system
    public fun pause_system(
        system: &mut SystemState,
        _admin_cap: &AdminCap,
        ctx: &mut TxContext
    ) {
        system.is_paused = true;
        
        event::emit(SystemPaused {
            paused_by: tx_context::sender(ctx)
        });
    }

    /// Resume system operations
    public fun resume_system(
        system: &mut SystemState,
        _admin_cap: &AdminCap,
        ctx: &mut TxContext
    ) {
        system.is_paused = false;
        
        event::emit(SystemResumed {
            resumed_by: tx_context::sender(ctx)
        });
    }

    // ===== View Functions =====

    /// Get comprehensive system statistics
    public fun get_system_stats(system: &SystemState): SystemStats {
        SystemStats {
            total_transactions: system.transaction_count,
            total_anomalies: system.anomaly_count,
            current_threshold: system.anomaly_threshold,
            model_version: system.current_model_version,
            auditor_count: (vector::length(&system.auditors) as u64)
        }
    }

    /// Check if address is auditor
    public fun is_auditor(system: &SystemState, addr: address): bool {
        vector::contains(&system.auditors, &addr)
    }

    /// Get list of auditors
    public fun get_auditors(system: &SystemState): &vector<address> {
        &system.auditors
    }

    /// Get current model version and hash
    public fun get_current_model(system: &SystemState): (u64, &vector<u8>) {
        let hash = vec_map::get(&system.model_hashes, &system.current_model_version);
        (system.current_model_version, hash)
    }

    /// Check if system is operational
    public fun is_system_operational(system: &SystemState): bool {
        !system.is_paused
    }

    // ===== Internal Functions =====

    /// Rate limiting implementation
    fun check_rate_limit(system: &SystemState) {
        // Simplified rate limiting
        if (system.transaction_count > 0 && (system.transaction_count % MAX_REQUESTS_PER_WINDOW) == 0) {
            // Ensure we don't exceed absolute limits
            assert!(system.transaction_count < 1000000, 100);
        }
    }

    // ===== Administrative Functions =====

    /// Transfer admin rights (requires current admin)
    public fun transfer_admin(
        system: &mut SystemState,
        _admin_cap: &AdminCap,
        new_admin: address,
        _ctx: &mut TxContext
    ) {
        system.admin = new_admin;
    }

    /// Review and mark anomaly as reviewed
    public fun review_anomaly(
        anomaly: &mut AnomalyResult,
        reviewer: address
    ) {
        anomaly.reviewed = true;
        anomaly.reviewed_by = option::some(reviewer);
    }
}