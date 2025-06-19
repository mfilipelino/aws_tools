"""Tests for the unified AWS client factory."""

import os
from unittest.mock import Mock, patch

from aws_clients import create_aws_client


@patch("aws_clients.boto3.Session")
def test_create_aws_client_with_defaults(mock_session):
    """Test creating a client with default parameters."""
    mock_client = Mock()
    mock_session_instance = Mock()
    mock_session_instance.client.return_value = mock_client
    mock_session.return_value = mock_session_instance

    result = create_aws_client("s3")

    # Should use default profile from environment or 'sandbox'
    mock_session.assert_called_once_with(profile_name="sandbox")
    mock_session_instance.client.assert_called_once_with("s3", region_name=None)
    assert result == mock_client


@patch("aws_clients.boto3.Session")
def test_create_aws_client_with_custom_profile(mock_session):
    """Test creating a client with custom profile."""
    mock_client = Mock()
    mock_session_instance = Mock()
    mock_session_instance.client.return_value = mock_client
    mock_session.return_value = mock_session_instance

    result = create_aws_client("kinesis", profile_name="custom-profile")

    mock_session.assert_called_once_with(profile_name="custom-profile")
    mock_session_instance.client.assert_called_once_with("kinesis", region_name=None)
    assert result == mock_client


@patch("aws_clients.boto3.Session")
def test_create_aws_client_with_region(mock_session):
    """Test creating a client with custom region."""
    mock_client = Mock()
    mock_session_instance = Mock()
    mock_session_instance.client.return_value = mock_client
    mock_session.return_value = mock_session_instance

    result = create_aws_client("glue", region_name="us-west-2")

    mock_session.assert_called_once_with(profile_name="sandbox")
    mock_session_instance.client.assert_called_once_with("glue", region_name="us-west-2")
    assert result == mock_client


@patch.dict(os.environ, {"PROFILE_NAME": "env-profile"})
@patch("aws_clients.boto3.Session")
def test_create_aws_client_uses_env_profile(mock_session):
    """Test that the client factory uses the PROFILE_NAME environment variable."""
    mock_client = Mock()
    mock_session_instance = Mock()
    mock_session_instance.client.return_value = mock_client
    mock_session.return_value = mock_session_instance

    result = create_aws_client("sagemaker")

    mock_session.assert_called_once_with(profile_name="env-profile")
    mock_session_instance.client.assert_called_once_with("sagemaker", region_name=None)
    assert result == mock_client


@patch("aws_clients.boto3.Session")
def test_create_aws_client_all_parameters(mock_session):
    """Test creating a client with all parameters specified."""
    mock_client = Mock()
    mock_session_instance = Mock()
    mock_session_instance.client.return_value = mock_client
    mock_session.return_value = mock_session_instance

    result = create_aws_client("cloudformation", profile_name="test-profile", region_name="eu-west-1")

    mock_session.assert_called_once_with(profile_name="test-profile")
    mock_session_instance.client.assert_called_once_with("cloudformation", region_name="eu-west-1")
    assert result == mock_client
