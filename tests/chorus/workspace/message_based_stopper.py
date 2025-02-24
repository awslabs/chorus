import unittest
from unittest.mock import MagicMock, patch

from chorus.workspace.stop_conditions import MessageBasedStopper
from chorus.data.dialog import Message
from chorus.environment.global_context import ChorusGlobalContext


class TestMessageBasedStopper(unittest.TestCase):
    def setUp(self):
        # Create a mock runner and global context for testing
        self.mock_runner = MagicMock()
        self.global_context = ChorusGlobalContext(process_manager=MagicMock())
        self.mock_runner.get_global_context.return_value = self.global_context

    def test_stop_on_exact_match(self):
        # Create a stopper that matches specific source, destination, and channel
        stopper = MessageBasedStopper(
            source="agent1",
            destination="agent2",
            channel="test_channel"
        )
        stopper.set_runner(self.mock_runner)

        # Send a matching message
        self.global_context.send_message(
            Message(
                source="agent1",
                destination="agent2",
                channel="test_channel",
                content="test message"
            )
        )

        # Stopper should return True
        self.assertTrue(stopper.stop())

    def test_no_stop_on_mismatch(self):
        # Create a stopper with specific criteria
        stopper = MessageBasedStopper(
            source="agent1",
            destination="agent2",
            channel="test_channel"
        )
        stopper.set_runner(self.mock_runner)

        # Send messages that don't fully match
        self.global_context.send_message(
            Message(
                source="agent1",
                destination="agent3",  # Different destination
                channel="test_channel",
                content="test message"
            )
        )
        self.global_context.send_message(
            Message(
                source="agent1",
                destination="agent2",
                channel="different_channel",  # Different channel
                content="test message"
            )
        )

        # Stopper should return False
        self.assertFalse(stopper.stop())

    def test_stop_with_partial_criteria(self):
        # Create a stopper that only checks channel
        stopper = MessageBasedStopper(channel="test_channel")
        stopper.set_runner(self.mock_runner)

        # Send a message with matching channel but different source/destination
        self.global_context.send_message(
            Message(
                source="any_agent",
                destination="any_other_agent",
                channel="test_channel",
                content="test message"
            )
        )

        # Stopper should return True since only channel matters
        self.assertTrue(stopper.stop())

    def test_no_messages(self):
        # Create a stopper with criteria
        stopper = MessageBasedStopper(
            source="agent1",
            destination="agent2",
            channel="test_channel"
        )
        stopper.set_runner(self.mock_runner)

        # No messages sent
        # Stopper should return False
        self.assertFalse(stopper.stop())


if __name__ == '__main__':
    unittest.main() 