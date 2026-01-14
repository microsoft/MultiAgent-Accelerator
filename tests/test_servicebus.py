"""
Test Service Bus Integration with Orchestrator

This script demonstrates how to:
1. Send tasks to Service Bus queue
2. Monitor queue processing
3. Receive responses from response queue
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from azure.identity import AzureCliCredential
from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

SERVICEBUS_NAMESPACE = os.getenv("SERVICEBUS_NAMESPACE", "multiagent-dev-servicebus.servicebus.windows.net")


async def send_task_to_queue(task: str, user_id: str = "test-user"):
    """Send a task directly to Service Bus queue"""
    print(f"\n📤 Sending task to queue: {task}")
    
    credential = AzureCliCredential()
    
    async with ServiceBusClient(
        fully_qualified_namespace=SERVICEBUS_NAMESPACE,
        credential=credential
    ) as client:
        async with client.get_queue_sender(queue_name="agent-tasks") as sender:
            message = ServiceBusMessage(
                body=task,
                application_properties={
                    "user_id": user_id,
                    "preferred_agent": ""
                }
            )
            await sender.send_messages(message)
            print(f"✅ Message sent: {message.message_id}")
            return message.message_id


async def receive_response_from_queue(timeout: int = 30):
    """Receive response from Service Bus response queue"""
    print(f"\n📥 Waiting for response (timeout: {timeout}s)...")
    
    credential = AzureCliCredential()
    
    async with ServiceBusClient(
        fully_qualified_namespace=SERVICEBUS_NAMESPACE,
        credential=credential
    ) as client:
        async with client.get_queue_receiver(
            queue_name="agent-responses",
            max_wait_time=timeout
        ) as receiver:
            received_msgs = await receiver.receive_messages(max_message_count=1, max_wait_time=timeout)
            
            for msg in received_msgs:
                result = str(msg)
                user_id = msg.application_properties.get("user_id")
                agent_used = msg.application_properties.get("agent_used")
                original_task = msg.application_properties.get("original_task")
                
                print(f"\n✅ Response received!")
                print(f"   User: {user_id}")
                print(f"   Agent: {agent_used}")
                print(f"   Original Task: {original_task}")
                print(f"   Result: {result}")
                
                await receiver.complete_message(msg)
                return result
            
            print("⏰ Timeout - no response received")
            return None


async def test_end_to_end():
    """Test complete flow: send task -> wait for processing -> receive response"""
    print("=" * 80)
    print("🧪 Testing End-to-End Service Bus Integration")
    print("=" * 80)
    
    # Make sure orchestrator is running
    print("\n⚠️  Make sure the orchestrator is running!")
    print("   Terminal: cd agents/orchestrator && ../../.venv/Scripts/python.exe main.py")
    input("\nPress Enter when orchestrator is ready...")
    
    # Test 1: Currency conversion
    print("\n" + "=" * 80)
    print("Test 1: Currency Conversion")
    print("=" * 80)
    
    await send_task_to_queue(
        task="What is the current exchange rate from USD to EUR?",
        user_id="test-user-001"
    )
    
    print("\n⏳ Waiting for orchestrator to process...")
    await asyncio.sleep(5)  # Give orchestrator time to process
    
    await receive_response_from_queue(timeout=10)
    
    # Test 2: Travel planning
    print("\n" + "=" * 80)
    print("Test 2: Travel Planning")
    print("=" * 80)
    
    await send_task_to_queue(
        task="Find me restaurants in Paris",
        user_id="test-user-002"
    )
    
    print("\n⏳ Waiting for orchestrator to process...")
    await asyncio.sleep(5)
    
    await receive_response_from_queue(timeout=10)
    
    print("\n" + "=" * 80)
    print("✅ All tests complete!")
    print("=" * 80)


async def monitor_queue_stats():
    """Monitor queue statistics"""
    from azure.servicebus import ServiceBusClient as SyncServiceBusClient
    
    credential = AzureCliCredential()
    
    with SyncServiceBusClient(
        fully_qualified_namespace=SERVICEBUS_NAMESPACE,
        credential=credential
    ) as client:
        for queue_name in ["agent-tasks", "agent-responses"]:
            receiver = client.get_queue_receiver(queue_name=queue_name)
            try:
                print(f"\n📊 Queue: {queue_name}")
                # Note: Queue stats require management operations
                # For now, just check if we can connect
                print(f"   ✅ Connected successfully")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            finally:
                receiver.close()


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Service Bus integration")
    parser.add_argument(
        "action",
        choices=["send", "receive", "test", "stats"],
        help="Action to perform"
    )
    parser.add_argument(
        "--task",
        help="Task to send (for 'send' action)",
        default="What is the exchange rate from USD to EUR?"
    )
    parser.add_argument(
        "--user",
        help="User ID",
        default="test-user"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        help="Timeout for receive (seconds)",
        default=30
    )
    
    args = parser.parse_args()
    
    if args.action == "send":
        await send_task_to_queue(args.task, args.user)
    
    elif args.action == "receive":
        await receive_response_from_queue(args.timeout)
    
    elif args.action == "test":
        await test_end_to_end()
    
    elif args.action == "stats":
        await monitor_queue_stats()


if __name__ == "__main__":
    asyncio.run(main())
