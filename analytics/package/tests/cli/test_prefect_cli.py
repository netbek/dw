from package.cli.prefect_cli import _build_deployment_actions, DeployAction, DeploymentAction

import unittest


class TestCreateDeployment(unittest.TestCase):
    def test_create_none_and_resume_none(self):
        selected_names = []
        existing_names = []

        actual = _build_deployment_actions(
            DeployAction.create, selected_names, existing_names
        )
        expected = []

        self.assertCountEqual(actual, expected)

    def test_create_all(self):
        selected_names = ["dep1", "dep2"]
        existing_names = []

        actual = _build_deployment_actions(
            DeployAction.create, selected_names, existing_names
        )
        expected = [
            {"action": DeployAction.create, "name": "dep1"},
            {"action": DeployAction.create, "name": "dep2"},
        ]

        self.assertCountEqual(actual, expected)

    def test_resume_all(self):
        selected_names = ["dep1", "dep2"]
        existing_names = ["dep1", "dep2"]

        actual = _build_deployment_actions(
            DeployAction.create, selected_names, existing_names
        )
        expected = [
            {"action": DeploymentAction.resume, "name": "dep1"},
            {"action": DeploymentAction.resume, "name": "dep2"},
        ]

        self.assertCountEqual(actual, expected)

    def test_create_some_and_resume_some(self):
        selected_names = ["dep1", "dep2"]
        existing_names = ["dep1"]

        actual = _build_deployment_actions(
            DeployAction.create, selected_names, existing_names
        )
        expected = [
            {"action": DeploymentAction.resume, "name": "dep1"},
            {"action": DeployAction.create, "name": "dep2"},
        ]

        self.assertCountEqual(actual, expected)


class TestDeleteDeployment(unittest.TestCase):
    def test_delete_none(self):
        selected_names = []
        existing_names = []

        actual = _build_deployment_actions(
            DeploymentAction.delete, selected_names, existing_names
        )
        expected = []

        self.assertCountEqual(actual, expected)

    def test_delete_all(self):
        selected_names = ["dep1", "dep2"]
        existing_names = ["dep1", "dep2"]

        actual = _build_deployment_actions(
            DeploymentAction.delete, selected_names, existing_names
        )
        expected = [
            {"action": DeploymentAction.delete, "name": "dep1"},
            {"action": DeploymentAction.delete, "name": "dep2"},
        ]

        self.assertCountEqual(actual, expected)

    def test_delete_some(self):
        selected_names = ["dep1"]
        existing_names = ["dep1", "dep2"]

        actual = _build_deployment_actions(
            DeploymentAction.delete, selected_names, existing_names
        )
        expected = [{"action": DeploymentAction.delete, "name": "dep1"}]

        self.assertCountEqual(actual, expected)


class TestPauseDeployment(unittest.TestCase):
    def test_pause_none(self):
        selected_names = []
        existing_names = []

        actual = _build_deployment_actions(
            DeploymentAction.pause, selected_names, existing_names
        )
        expected = []

        self.assertCountEqual(actual, expected)

    def test_pause_all(self):
        selected_names = ["dep1", "dep2"]
        existing_names = ["dep1", "dep2"]

        actual = _build_deployment_actions(
            DeploymentAction.pause, selected_names, existing_names
        )
        expected = [
            {"action": DeploymentAction.pause, "name": "dep1"},
            {"action": DeploymentAction.pause, "name": "dep2"},
        ]

        self.assertCountEqual(actual, expected)

    def test_pause_some(self):
        selected_names = ["dep1"]
        existing_names = ["dep1", "dep2"]

        actual = _build_deployment_actions(
            DeploymentAction.pause, selected_names, existing_names
        )
        expected = [{"action": DeploymentAction.pause, "name": "dep1"}]

        self.assertCountEqual(actual, expected)


class TestResumeDeployment(unittest.TestCase):
    def test_resume_none(self):
        selected_names = []
        existing_names = []

        actual = _build_deployment_actions(
            DeploymentAction.resume, selected_names, existing_names
        )
        expected = []

        self.assertCountEqual(actual, expected)

    def test_resume_all(self):
        selected_names = ["dep1", "dep2"]
        existing_names = ["dep1", "dep2"]

        actual = _build_deployment_actions(
            DeploymentAction.resume, selected_names, existing_names
        )
        expected = [
            {"action": DeploymentAction.resume, "name": "dep1"},
            {"action": DeploymentAction.resume, "name": "dep2"},
        ]

        self.assertCountEqual(actual, expected)

    def test_resume_some(self):
        selected_names = ["dep1"]
        existing_names = ["dep1", "dep2"]

        actual = _build_deployment_actions(
            DeploymentAction.resume, selected_names, existing_names
        )
        expected = [{"action": DeploymentAction.resume, "name": "dep1"}]

        self.assertCountEqual(actual, expected)
