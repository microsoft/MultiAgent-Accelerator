#!/usr/bin/env python3
"""
Retrieve responses from Service Bus agent-responses queue

This script receives and displays responses from async task processing.
"""

import asyncio
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from azure.identity.aio import AzureCliCredential
from azure.servicebus.aio import ServiceBusClient

SERVICEBUS_NAMESPACE = "multiagent-dev-servicebus.servicebus.windows.net"


async def receive_responses(count: int = 1, timeout: int = 30):
    """Receive responses from the agent-responses queue"""
    print(f"📥 Waiting for up to {count} response(s) (timeout: {timeout}s)...\n")
    
    credential = AzureCliCredential()
    
    async with ServiceBusClient(
        fully_qualified_namespace=SERVICEBUS_NAMESPACE,
        credential=credential
    ) as client:
        async with client.get_queue_receiver(
            queue_name="agent-responses",
            max_wait_time=timeout
        ) as receiver:
            
            messages = await receiver.receive_messages(
                max_message_count=count,
                max_wait_time=timeout
            )
            
            if not messages:
                print("⏰ No responses received within timeout period")
                return
            
            for i, msg in enumerate(messages, 1):
                result = str(msg)
                user_id = msg.application_properties.get("user_id", "unknown")
                agent = msg.application_properties.get("agent_used", "unknown")
                task = msg.application_properties.get("original_task", "N/A")
                
                print(f"{'='*80}")
                print(f"📬 Response {i}/{len(messages)}")
                print(f"{'='*80}")
                print(f"User ID:       {user_id}")
                print(f"Agent:         {agent}")
                print(f"Original Task: {task}")
                print(f"\n💬 Result:\n{result}")
                print(f"{'='*80}\n")
                
                # Complete the message to remove it from queue
                await receiver.complete_message(msg)
            
            print(f"✅ Received and processed {len(messages)} response(s)")


async def peek_responses(count: int = 10):
    """Peek at responses without removing them from queue"""
    print(f"👀 Peeking at up to {count} response(s)...\n")
    
    credential = AzureCliCredential()
    
    async with ServiceBusClient(
        fully_qualified_namespace=SERVICEBUS_NAMESPACE,
        credential=credential
    ) as client:
        async with client.get_queue_receiver(
            queue_name="agent-responses"
        ) as receiver:
            
            messages = await receiver.peek_messages(max_message_count=count)
            
            if not messages:
                print("📭 No messages in queue")
                return
            
            for i, msg in enumerate(messages, 1):
                result = str(msg)
                user_id = msg.application_properties.get("user_id", "unknown")
                agent = msg.application_properties.get("agent_used", "unknown")
                
                print(f"{'='*80}")
                print(f"📬 Response {i}/{len(messages)}")
                print(f"{'='*80}")
                print(f"User ID: {user_id}")
                print(f"Agent:   {agent}")
                print(f"\n💬 Result (truncated):\n{result[:200]}...")
                print(f"{'='*80}\n")
            
            print(f"👁️  Peeked at {len(messages)} response(s) (not removed from queue)")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Receive async task responses from Service Bus"
    )
    parser.add_argument(
        "action",
        choices=["receive", "peek"],
        default="receive",
        nargs="?",
        help="Action: receive (and remove) or peek (view only)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of messages to retrieve (default: 1)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout in seconds for receive (default: 30)"
    )
    
    args = parser.parse_args()
    
    if args.action == "peek":
        await peek_responses(args.count)
    else:
        await receive_responses(args.count, args.timeout)


if __name__ == "__main__":
    asyncio.run(main())
