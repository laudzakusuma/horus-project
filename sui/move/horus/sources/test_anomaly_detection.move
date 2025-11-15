#[test_only]
module horus::test_anomaly_detection {
    use sui::test_scenario;
    use std::vector;
    use horus::anomaly_detection;

    #[test]
    fun test_initialize_system() {
        let admin = @0xA;
        let scenario = test_scenario::begin(admin);
        
        // Initialize system
        anomaly_detection::initialize(
            admin,
            75, // threshold
            b"model_v1_hash_123456789", // model_hash
            test_scenario::ctx(&mut scenario)
        );

        test_scenario::end(scenario);
    }

    #[test]
    fun test_complete_workflow() {
        let admin = @0xA;
        let scenario = test_scenario::begin(admin);
        
        // Initialize system
        anomaly_detection::initialize(
            admin,
            75,
            b"model_v1_hash_123456789",
            test_scenario::ctx(&mut scenario)
        );

        // Get admin capability from admin's address
        let admin_cap = test_scenario::take_from_address<anomaly_detection::AdminCap>(&scenario, admin);
        let system = test_scenario::take_shared<anomaly_detection::SystemState>(&scenario);
        
        // Add auditor
        anomaly_detection::add_auditor(
            &mut system,
            &admin_cap,
            @0xB, // auditor
            test_scenario::ctx(&mut scenario)
        );

        // Record normal transaction
        anomaly_detection::record_transaction(
            &mut system,
            b"tx_normal_001",
            b"transfer",
            1000,
            b"metadata",
            25, // low risk
            test_scenario::ctx(&mut scenario)
        );

        // Report anomaly
        anomaly_detection::report_anomaly_score(
            &mut system,
            b"tx_suspicious_001",
            vector[85, 90, 95, 100], // high risk features
            1, // model_version
            90, // high anomaly score
            test_scenario::ctx(&mut scenario)
        );

        // Update threshold
        anomaly_detection::update_threshold(
            &mut system,
            &admin_cap,
            85, // new threshold
            test_scenario::ctx(&mut scenario)
        );

        test_scenario::return_shared(system);
        test_scenario::return_to_address(&scenario, admin, admin_cap);
        test_scenario::end(scenario);
    }

    #[test]
    fun test_emergency_pause_resume() {
        let admin = @0xA;
        let scenario = test_scenario::begin(admin);
        
        anomaly_detection::initialize(
            admin,
            75,
            b"model_v1",
            test_scenario::ctx(&mut scenario)
        );

        let admin_cap = test_scenario::take_from_address<anomaly_detection::AdminCap>(&scenario, admin);
        let system = test_scenario::take_shared<anomaly_detection::SystemState>(&scenario);
        
        // Pause system
        anomaly_detection::pause_system(
            &mut system,
            &admin_cap,
            test_scenario::ctx(&mut scenario)
        );

        assert!(!anomaly_detection::is_system_operational(&system), 0);

        // Resume system
        anomaly_detection::resume_system(
            &mut system,
            &admin_cap,
            test_scenario::ctx(&mut scenario)
        );

        assert!(anomaly_detection::is_system_operational(&system), 0);

        test_scenario::return_shared(system);
        test_scenario::return_to_address(&scenario, admin, admin_cap);
        test_scenario::end(scenario);
    }

    #[test]
    #[expected_failure(abort_code = 2, location = horus::anomaly_detection)]
    fun test_invalid_threshold() {
        let admin = @0xA;
        let scenario = test_scenario::begin(admin);
        
        // This should fail - threshold too low
        anomaly_detection::initialize(
            admin,
            5, // invalid threshold (too low)
            b"model_v1",
            test_scenario::ctx(&mut scenario)
        );

        test_scenario::end(scenario);
    }

    #[test]
    fun test_model_versioning() {
        let admin = @0xA;
        let scenario = test_scenario::begin(admin);
        
        anomaly_detection::initialize(
            admin,
            75,
            b"model_v1_hash",
            test_scenario::ctx(&mut scenario)
        );

        let admin_cap = test_scenario::take_from_address<anomaly_detection::AdminCap>(&scenario, admin);
        let system = test_scenario::take_shared<anomaly_detection::SystemState>(&scenario);
        
        // Update model
        anomaly_detection::update_model(
            &mut system,
            &admin_cap,
            b"model_v2_hash_improved",
            test_scenario::ctx(&mut scenario)
        );

        let (version, hash) = anomaly_detection::get_current_model(&system);
        assert!(version == 2, 0);
        assert!(*hash == b"model_v2_hash_improved", 0);

        test_scenario::return_shared(system);
        test_scenario::return_to_address(&scenario, admin, admin_cap);
        test_scenario::end(scenario);
    }

    #[test]
    fun test_auditor_management_limits() {
        let admin = @0xA;
        let scenario = test_scenario::begin(admin);
        
        anomaly_detection::initialize(
            admin,
            75,
            b"model_v1",
            test_scenario::ctx(&mut scenario)
        );

        let admin_cap = test_scenario::take_from_address<anomaly_detection::AdminCap>(&scenario, admin);
        let system = test_scenario::take_shared<anomaly_detection::SystemState>(&scenario);
        
        // Add one auditor
        anomaly_detection::add_auditor(
            &mut system,
            &admin_cap,
            @0xB,
            test_scenario::ctx(&mut scenario)
        );

        let auditors = anomaly_detection::get_auditors(&system);
        let auditor_count = vector::length(auditors);
        assert!(auditor_count == 1, 0);

        test_scenario::return_shared(system);
        test_scenario::return_to_address(&scenario, admin, admin_cap);
        test_scenario::end(scenario);
    }

    #[test]
    fun test_auditor_verification() {
        let admin = @0xA;
        let auditor = @0xB;
        let non_auditor = @0xC;
        let scenario = test_scenario::begin(admin);
        
        anomaly_detection::initialize(
            admin,
            75,
            b"model_v1",
            test_scenario::ctx(&mut scenario)
        );

        let admin_cap = test_scenario::take_from_address<anomaly_detection::AdminCap>(&scenario, admin);
        let system = test_scenario::take_shared<anomaly_detection::SystemState>(&scenario);
        
        // Add auditor
        anomaly_detection::add_auditor(
            &mut system,
            &admin_cap,
            auditor,
            test_scenario::ctx(&mut scenario)
        );

        // Verify auditor was added
        assert!(anomaly_detection::is_auditor(&system, auditor), 0);
        
        // Verify non-auditor is not recognized
        assert!(!anomaly_detection::is_auditor(&system, non_auditor), 0);

        test_scenario::return_shared(system);
        test_scenario::return_to_address(&scenario, admin, admin_cap);
        test_scenario::end(scenario);
    }
}