import { useState } from 'react';
import { Box, Text, Heading, Button, Input, Center } from "@chakra-ui/react";

export default function Home() {
  const [videoLink, setVideoLink] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const handleVideoLinkChange = (e) => {
    setVideoLink(e.target.value);
    setErrorMessage("");  // Clear any previous errors
  };

  const handleSubmit = async () => {
    // Basic YouTube link validation
    const youtubeRegex = /^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$/;
    if (!youtubeRegex.test(videoLink)) {
      setErrorMessage("Please enter a valid YouTube link.");
      return;
    }

    try {
      // Send the video link to the /apply-sfx endpoint at port 8000
      const response = await fetch('http://localhost:8000/apply-sfx', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ videoLink }),
      });

      if (!response.ok) {
        throw new Error("Failed to send video link to process.");
      }

      // Set the form as submitted on successful response
      setSubmitted(true);

    } catch (error) {
      setErrorMessage("Failed to send the video for processing. Try again.");
    }
  };

  const handleTryNewVideo = () => {
    setVideoLink("");
    setSubmitted(false);
    setErrorMessage("");
  };

  return (
    <Box 
      minHeight="100vh" 
      bg="#2B303A" 
      textAlign="center" 
      color="white" 
      display="flex" 
      flexDirection="column" 
      justifyContent="center" 
      alignItems="center"
      p={5}
    >
      <Center>
        <Heading 
          as="h1" 
          size="3xl" 
          color="#C5FFA6" 
          fontWeight="bold"
          mb={4}
        >
          SoundSeq
        </Heading>
      </Center>

      {!submitted ? (
        <>
          <Text fontSize="xl" mb={6} color="#C5FFA6">
          Apply SFX Intelligently Across Your Edits
          </Text>

          {/* Video Link Input */}
          <Input 
            placeholder="Enter YouTube link"
            value={videoLink}
            onChange={handleVideoLinkChange}
            size="lg"
            width="400px"
            mb={4}
            color="white"
            bg="#3B3F45"
            borderColor="#C5FFA6"
          />

          {/* Display error message if invalid YouTube link */}
          {errorMessage && (
            <Text color="red.400" mb={4}>
              {errorMessage}
            </Text>
          )}

          {/* Submit Button */}
          <Button
            onClick={handleSubmit}
            bg="#C5FFA6"
            _hover={{ bg: "#A4E694" }}
            color="#2B303A" 
            fontSize="lg" 
            px={10} 
            py={6} 
            rounded="md"
            transition="0.2s"
          >
            Submit
          </Button>
        </>
      ) : (
        <>
          {/* Confirmation Message */}
          <Text fontSize="xl" color="#C5FFA6" mb={6}>
            Your video has been sent to process!
          </Text>

          {/* Try New Video Button */}
          <Button
            onClick={handleTryNewVideo}
            bg="#C5FFA6"
            _hover={{ bg: "#A4E694" }}
            color="#2B303A" 
            fontSize="lg" 
            px={10} 
            py={6} 
            rounded="md"
            transition="0.2s"
          >
            Try New Video
          </Button>
        </>
      )}
    </Box>
  );
}