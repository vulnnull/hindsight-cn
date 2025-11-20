"""Test MCP server with real server and client."""

import asyncio
import os
import pytest
from mcp import ClientSession
from mcp.client.sse import sse_client


# Note: MCP server tests now require the full web server to be running
# with MEMORA_API_MCP_ENABLED=true since there's no standalone MCP server anymore.
# These tests are kept for documentation but may need manual server setup.

pytest.skip("MCP server is now integrated with web server. Run web server with MEMORA_API_MCP_ENABLED=true to test.", allow_module_level=True)


@pytest.mark.asyncio
async def test_mcp_server_tools_via_sse(mcp_server):
    """Test MCP server tools via SSE transport using proper MCP client."""
    sse_url = mcp_server

    async with sse_client(sse_url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test 1: List tools
            tools_list = await session.list_tools()
            print(f"Tools: {tools_list}")
            tool_names = [t.name for t in tools_list.tools]
            assert "memora_search" in tool_names
            assert "memora_put" in tool_names

            # Test 2: Call memora_put
            put_result = await session.call_tool(
                "memora_put",
                arguments={
                    "content": "User loves Python programming",
                    "context": "programming_preferences",
                    "explanation": "Storing user's programming language preference"
                }
            )
            print(f"Put result: {put_result}")
            assert put_result is not None

            # Wait a bit for indexing
            await asyncio.sleep(1)

            # Test 3: Call memora_search
            search_result = await session.call_tool(
                "memora_search",
                arguments={
                    "query": "What programming languages does the user like?",
                    "max_tokens": 4096,
                    "explanation": "Searching for programming preferences"
                }
            )
            print(f"Search result: {search_result}")
            assert search_result is not None


@pytest.mark.asyncio
async def test_multiple_concurrent_requests(mcp_server):
    """Test multiple concurrent requests from a single session."""
    sse_url = mcp_server

    async with sse_client(sse_url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Fire off 10 concurrent search requests from same session
            async def make_search(idx):
                try:
                    result = await session.call_tool(
                        "memora_search",
                        arguments={
                            "query": f"test query {idx}",
                            "explanation": f"Concurrent test {idx}"
                        }
                    )
                    return idx, "success", result
                except Exception as e:
                    return idx, "error", str(e)

            tasks = [make_search(i) for i in range(10)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check results
            successes = 0
            failures = 0

            for result in results:
                if isinstance(result, Exception):
                    print(f"Request failed with exception: {result}")
                    failures += 1
                else:
                    idx, status, data = result
                    if status == "success":
                        successes += 1
                    else:
                        print(f"Request {idx} failed: {data}")
                        failures += 1

            print(f"Successes: {successes}, Failures: {failures}")

            # We expect all requests to succeed
            assert successes >= 8, f"Too many failures: {failures}/10"


@pytest.mark.asyncio
async def test_race_condition_with_rapid_requests(mcp_server):
    """Test rapid-fire requests with multiple sessions to trigger race condition."""
    sse_url = mcp_server

    async def rapid_session_search(idx):
        """Create a new session and immediately make a request."""
        try:
            async with sse_client(sse_url) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    # Make request immediately after initialization
                    result = await session.call_tool(
                        "memora_search",
                        arguments={
                            "query": f"rapid query {idx}",
                            "max_tokens": 2048
                        }
                    )
                    return idx, "success", result
        except Exception as e:
            return idx, "error", str(e)

    # Fire 20 requests with minimal delay, each with its own session
    tasks = [rapid_session_search(i) for i in range(20)]
    results = await asyncio.gather(*tasks)

    # Analyze results
    errors = []
    for idx, status, data in results:
        if status == "error":
            errors.append((idx, data))

    if errors:
        print(f"Found {len(errors)} errors:")
        for idx, error_msg in errors:
            print(f"  Request {idx}: {error_msg}")

    # Most requests should succeed
    assert len(errors) < 5, f"Too many errors: {len(errors)}/20"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
